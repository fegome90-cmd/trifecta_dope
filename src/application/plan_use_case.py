"""Plan Use Case - PRIME-only planning with 3-level matching."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class PlanUseCase:
    """Generate execution plan using PRIME index only (no RAG).

    Matching Levels:
    - L1: Explicit feature id (feature:<id>)
    - L2: Alias match (structured triggers from aliases.yaml)
    - L3: Fallback to entrypoints
    """

    def __init__(self, file_system: Any, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def _hash_task(self, task: str) -> str:
        """Generate SHA256 hash of task for privacy."""
        return hashlib.sha256(task.encode()).hexdigest()[:16]

    def _normalize_task(self, task: str) -> str:
        """Normalize task using closed verb pattern list.

        Rules:
        - Lowercase and strip punctuation
        - Normalize verb patterns to canonical forms
        - Return normalized task for matching

        Verb normalizations (CLOSED LIST - no additions without review):
        - "show me" → "show"
        - "locate" → "locate"
        - "where is" → "where"
        - "where's" → "where"
        - "where are" → "where"
        - "walk through" → "walkthrough"
        - "walk me through" → "walkthrough"
        - "explain" → "explain"
        - "describe" → "describe"
        - "can you" → "" (remove)
        - "could you" → "" (remove)
        - "please" → "" (remove)
        """
        import string

        # Lowercase
        normalized = task.lower()

        # Strip leading/trailing punctuation
        normalized = normalized.strip(string.punctuation + " ")

        # Apply verb normalizations (order matters - longer patterns first)
        verb_map = {
            "walk me through": "walkthrough",
            "walk through": "walkthrough",
            "where are": "where",
            "where's": "where",
            "where is": "where",
            "can you": "",
            "could you": "",
            "please": "",
        }

        for pattern, replacement in verb_map.items():
            normalized = normalized.replace(pattern, replacement)

        # Clean up extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def _tokenize(self, text: str) -> set[str]:
        """Simple tokenization: lowercase, split on non-letters."""
        return set(re.findall(r"\w+", text.lower()))

    def _load_aliases(self, ctx_dir: Path) -> dict:
        """Load aliases.yaml for L2 matching."""
        aliases_path = ctx_dir / "aliases.yaml"

        if not aliases_path.exists():
            return {}

        try:
            content = aliases_path.read_text()
            data = json.loads(content) if content.startswith("{") else self._parse_yaml(content)

            # Check schema version
            if data.get("schema_version") == 2:
                return data.get("features", {})
        except Exception:
            pass

        return {}

    def _parse_yaml(self, content: str) -> dict:
        """Simple YAML parser for aliases.yaml structure."""
        # This is a minimal YAML parser for our specific structure
        # For production, use proper YAML library
        import yaml

        try:
            return yaml.safe_load(content)
        except ImportError:
            # Fallback: return empty dict if yaml not available
            return {}

    def _match_l1_explicit_feature(self, task: str, available_features: set[str]) -> str | None:
        """L1: Match explicit feature:<id> syntax.

        Args:
            task: User task string
            available_features: Set of valid feature IDs from aliases.yaml

        Returns:
            Feature ID if match found and valid, None otherwise
        """
        match = re.search(r"feature:(\w+)", task.lower())

        if not match:
            return None

        feature_id = match.group(1)

        # Fail-closed: feature must exist
        if feature_id not in available_features:
            return None

        return feature_id

    def _match_l2_alias(
        self, task: str, features: dict
    ) -> tuple[str | None, int, str | None]:
        """L2: Alias match with structured triggers.

        Args:
            task: User task string
            features: Dict from aliases.yaml (feature_id -> config)

        Returns:
            (feature_id, match_terms_count, matched_trigger_phrase)
        """
        task_tokens = self._tokenize(task)

        best_match = None
        best_score = 0
        best_trigger_phrase = None
        best_priority = 0

        for feature_id, config in features.items():
            triggers = config.get("triggers", [])
            priority = config.get("priority", 1)

            for trigger in triggers:
                phrase = trigger.get("phrase", "")
                terms = trigger.get("terms", [])
                high_signal = trigger.get("high_signal", False)

                # Check if task contains the phrase
                phrase_lower = phrase.lower()
                phrase_tokens = self._tokenize(phrase)

                # Count matching terms
                matching_terms = sum(1 for t in terms if t.lower() in task_tokens)

                # High signal triggers auto-match if any term matches
                if high_signal and matching_terms >= 1:
                    if priority > best_priority or (priority == best_priority and matching_terms > best_score):
                        best_match = feature_id
                        best_score = matching_terms
                        best_trigger_phrase = phrase
                        best_priority = priority
                    continue

                # Standard triggers require >= 2 term matches
                if matching_terms >= 2:
                    if priority > best_priority or (priority == best_priority and matching_terms > best_score):
                        best_match = feature_id
                        best_score = matching_terms
                        best_trigger_phrase = phrase
                        best_priority = priority

        if best_score == 0:
            return None, 0, None

        return best_match, best_score, best_trigger_phrase

    def _parse_prime_entrypoints(self, prime_path: Path) -> list[dict]:
        """Parse PRIME file to extract index.entrypoints."""
        content = prime_path.read_text()

        entrypoints = []

        # Find index.entrypoints section
        entrypoints_match = re.search(
            r"### index\.entrypoints.*?\n\n(.*?)###", content, re.DOTALL
        )
        if entrypoints_match:
            table_text = entrypoints_match.group(1)
            # Parse table rows
            rows = re.findall(r"\| `([^`]+)`\s+\| ([^|]+)\s+\|", table_text)
            for path, reason in rows:
                entrypoints.append({"path": path, "reason": reason})

        return entrypoints

    def _get_bundle_for_feature(self, feature_id: str, features: dict) -> dict:
        """Get bundle (chunks + paths + anchors) for a feature.

        Args:
            feature_id: Feature identifier
            features: Dict from aliases.yaml

        Returns:
            Dict with chunks (list), paths (list), anchors (list)
        """
        if feature_id not in features:
            return {"chunks": [], "paths": [], "anchors": []}

        bundle = features[feature_id].get("bundle", {})
        chunks = bundle.get("chunks", [])
        paths = bundle.get("paths", [])
        anchors = bundle.get("anchors", [])

        return {"chunks": chunks, "paths": paths, "anchors": anchors}

    def _verify_bundle_assertions(
        self, feature_id: str, bundle: dict, target_path: Path
    ) -> tuple[bool, dict]:
        """Verify bundle assertions (paths exist, anchors in files).

        Args:
            feature_id: Feature identifier
            bundle: Dict with chunks, paths, anchors
            target_path: Path to segment directory

        Returns:
            (assertions_ok, assertion_result) where assertion_result contains:
            - ok: bool
            - failed_paths: list of paths that don't exist
            - failed_anchors: list of anchors not found in files
        """
        failed_paths = []
        failed_anchors = []

        paths = bundle.get("paths", [])
        anchors = bundle.get("anchors", [])

        # Check each path exists
        for path_str in paths:
            path = target_path / path_str
            if not path.exists():
                failed_paths.append(path_str)

        # Check each anchor appears in at least one path file
        for anchor in anchors:
            anchor_found = False
            for path_str in paths:
                path = target_path / path_str
                if path.exists():
                    try:
                        content = path.read_text()
                        if anchor in content:
                            anchor_found = True
                            break
                    except Exception:
                        pass
            if not anchor_found:
                failed_anchors.append(anchor)

        assertions_ok = len(failed_paths) == 0 and len(failed_anchors) == 0

        return (
            assertions_ok,
            {
                "ok": assertions_ok,
                "failed_paths": failed_paths,
                "failed_anchors": failed_anchors,
            },
        )

    def execute(self, target_path: Path, task: str) -> dict:
        """Generate execution plan for a task.

        Args:
            target_path: Path to segment directory
            task: User task description

        Returns:
            Plan dict with selected_feature, plan_hit, selected_by, bundle, next_steps, budget_est
        """
        import time

        start_time = time.time()

        if self.telemetry:
            self.telemetry.incr("ctx_plan_count")

        ctx_dir = target_path / "_ctx"

        # Load aliases for L2 matching
        features = self._load_aliases(ctx_dir)
        available_features = set(features.keys())

        # Initialize result
        result = {
            "selected_feature": None,
            "plan_hit": False,
            "selected_by": None,  # "feature" (L1) | "alias" (L2) | "fallback" (L3)
            "match_terms_count": 0,
            "matched_trigger": None,
            "chunk_ids": [],
            "paths": [],
            "next_steps": [],
            "budget_est": {"tokens": 0, "why": "No features available"},
            "task_hash": self._hash_task(task),
            "latency_ms": 0,
        }

        # No features available - fail fast
        if not available_features:
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            return result

        # Normalize task for L2 matching (T9.3)
        normalized_task = self._normalize_task(task)

        # === L1: Explicit feature id ===
        feature_id = self._match_l1_explicit_feature(task, available_features)

        if feature_id:
            result["selected_feature"] = feature_id
            result["plan_hit"] = True
            result["selected_by"] = "feature"
            result["budget_est"]["why"] = f"L1: Explicit feature:{feature_id}"
        else:
            # === L2: Alias match (using normalized task) ===
            feature_id, match_score, trigger_phrase = self._match_l2_alias(normalized_task, features)

            if feature_id:
                result["selected_feature"] = feature_id
                result["plan_hit"] = True
                result["selected_by"] = "alias"
                result["match_terms_count"] = match_score
                result["matched_trigger"] = trigger_phrase
                result["budget_est"]["why"] = f"L2: Alias match via '{trigger_phrase}' ({match_score} terms)"
            else:
                # === L3: Fallback to entrypoints ===
                result["selected_by"] = "fallback"
                result["budget_est"]["why"] = "L3: No feature match, using entrypoints"

        # Generate bundle and next_steps
        if result["plan_hit"]:
            bundle = self._get_bundle_for_feature(result["selected_feature"], features)

            # T9.3.1: Verify bundle assertions (paths exist, anchors in files)
            assertions_ok, assertion_result = self._verify_bundle_assertions(
                result["selected_feature"], bundle, target_path
            )

            if not assertions_ok:
                # Bundle assertions failed - degrade to fallback
                failed_feature_id = result["selected_feature"]  # Save before clearing
                result["plan_hit"] = False
                result["selected_feature"] = None
                result["selected_by"] = "fallback"
                result["bundle_assert_ok"] = False
                result["bundle_assert_failed_paths"] = assertion_result["failed_paths"]
                result["bundle_assert_failed_anchors"] = assertion_result["failed_anchors"]
                result["budget_est"]["why"] = f"L3: Bundle assertions failed for {failed_feature_id}, using entrypoints"
            else:
                # Assertions passed - use the bundle
                result["bundle_assert_ok"] = True

                # Parse chunk IDs
                chunks_str = ", ".join(bundle["chunks"])
                result["chunk_ids"] = [cid.strip() for cid in re.findall(r"`?([^:,`]+)`?", chunks_str)]
                result["paths"] = bundle["paths"]

                # Generate next steps
                if any(kw in task.lower() for kw in ["implement", "add", "create"]):
                    result["next_steps"].append({"action": "implement", "target": result["paths"][0] if result["paths"] else "."})
                else:
                    result["next_steps"].append({"action": "read", "target": result["paths"][0] if result["paths"] else "."})

                # Estimate tokens
                chunk_count = len(result["chunk_ids"])
                budget_tokens = chunk_count * 300  # ~300 tokens per chunk
                result["budget_est"]["tokens"] = budget_tokens

        else:
            # Fallback: use entrypoints from PRIME
            result["bundle_assert_ok"] = None  # Not applicable for direct fallback
            prime_files = list(ctx_dir.glob("prime_*.md"))

            if prime_files:
                entrypoints = self._parse_prime_entrypoints(prime_files[0])

                # Add entrypoint paths
                for ep in entrypoints[:5]:  # Max 5 entrypoints
                    result["paths"].append(ep["path"])

                result["next_steps"].append({"action": "read", "target": "README.md"})
                result["next_steps"].append({"action": "read", "target": "skill.md"})

                budget_tokens = 300
                result["budget_est"]["tokens"] = budget_tokens

        result["latency_ms"] = int((time.time() - start_time) * 1000)

        # Log telemetry
        if self.telemetry:
            telemetry_attrs = {
                "plan_hit": result["plan_hit"],
                "selected_feature": result["selected_feature"] or "",
                "selected_by": result["selected_by"] or "",
                "match_terms_count": result["match_terms_count"],
                "returned_chunks_count": len(result["chunk_ids"]),
                "returned_paths_count": len(result["paths"]),
            }

            # T9.3.1: Include bundle assertion status if applicable
            if "bundle_assert_ok" in result:
                telemetry_attrs["bundle_assert_ok"] = result["bundle_assert_ok"]
                if not result["bundle_assert_ok"]:
                    telemetry_attrs["bundle_assert_failed_paths"] = result.get("bundle_assert_failed_paths", [])
                    telemetry_attrs["bundle_assert_failed_anchors"] = result.get("bundle_assert_failed_anchors", [])

            self.telemetry.event(
                "ctx.plan",
                {"task_hash": result["task_hash"]},
                telemetry_attrs,
                result["latency_ms"],
            )

        return result
