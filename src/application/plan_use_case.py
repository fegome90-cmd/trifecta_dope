"""Plan Use Case - PRIME-only planning with 4-level matching."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class PlanUseCase:
    """Generate execution plan using PRIME index only (no RAG).

    Matching Levels (T9.3.2):
    - L1: Explicit feature id (feature:<id>) - highest priority
    - L2: Direct NL trigger match (canonical intent phrases from nl_triggers[])
    - L3: Alias match (structured triggers from aliases.yaml with term counting)
    - L4: Fallback to entrypoints
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

    def _normalize_nl(self, task: str) -> list[str]:
        """Normalize NL query for L2 direct trigger matching.

        Rules (T9.3.2):
        - Lowercase
        - Strip punctuation
        - Collapse whitespace
        - Generate bigrams (2-token sequences)

        Args:
            task: Raw user task string

        Returns:
            List of normalized unigrams and bigrams
        """
        import string

        # Lowercase
        normalized = task.lower()

        # Strip punctuation
        normalized = normalized.translate(str.maketrans("", "", string.punctuation))

        # Collapse whitespace
        normalized = " ".join(normalized.split())

        # Generate unigrams and bigrams
        tokens = normalized.split()
        unigrams = tokens
        bigrams = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]

        return unigrams + bigrams

    def _tokenize(self, text: str) -> set[str]:
        """Simple tokenization: lowercase, split on non-letters."""
        return set(re.findall(r"\w+", text.lower()))

    def _load_aliases(self, ctx_dir: Path) -> dict:
        """Load aliases.yaml for L2/L3 matching."""
        aliases_path = ctx_dir / "aliases.yaml"

        if not aliases_path.exists():
            return {}

        try:
            content = aliases_path.read_text()
            data = json.loads(content) if content.startswith("{") else self._parse_yaml(content)

            # Check schema version (T9.3.2: support v3 with nl_triggers)
            schema_version = data.get("schema_version", 1)
            if schema_version >= 2:
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

    def _match_l2_nl_triggers(
        self, task: str, features: dict
    ) -> tuple[str | None, str | None, str | None, int, str | None, dict]:
        """L2: Direct NL trigger match with scoring and guardrails (T9.3.5).

        Args:
            task: User task string
            features: Dict from aliases.yaml (feature_id -> config)

        Returns:
            (feature_id, matched_trigger, warning, score, match_mode, debug_info)
            - feature_id: Matched feature ID or None
            - matched_trigger: The trigger phrase that matched
            - warning: Warning string or None (ambiguous_single_word_triggers | match_tie_fallback |
              weak_single_word_trigger)
            - score: Match score (2=exact, 1=subset, 0=no match)
            - match_mode: "exact" | "subset" | None
            - debug_info: L2 selection diagnostics

        Matching rules (T9.3.5):
        - score=2: Exact phrase match in ngrams
        - score=1: All trigger words present (subset match)
        - score=0: No match
        - Single-word guardrail: Only allowed if priority >= 4 AND no conflicts
        - Single-word clamp: If top candidate lacks support terms, fallback with warning
        - Ranking: (score, specificity, priority)
        - Tie in (score, specificity, priority) → fallback with warning
        """
        # Normalize task to unigrams + bigrams
        nl_ngrams = self._normalize_nl(task)
        task_tokens = self._tokenize(task)

        # Track all candidates with their scores
        candidates = []  # List of (feature_id, trigger, score, priority, match_mode, specificity, support_terms_present, support_terms_required, is_single_word)
        single_word_hits = []  # Track single-word trigger hits for guardrail

        for feature_id in sorted(features.keys()):  # Stable lexical order
            config = features[feature_id]
            nl_triggers = config.get("nl_triggers", [])
            priority = config.get("priority", 1)
            support_terms = [term.lower() for term in config.get("support_terms", [])]

            for trigger in nl_triggers:
                trigger_lower = trigger.lower().strip()
                trigger_words = set(trigger_lower.split())
                specificity = len(trigger_words)

                # Check if single-word trigger
                is_single_word = specificity == 1
                support_terms_required = is_single_word and priority >= 4
                support_terms_present = []
                if support_terms_required:
                    support_terms_present = sorted(
                        term
                        for term in support_terms
                        if term in task_tokens and term != trigger_lower
                    )

                # Scoring logic
                score = 0
                match_mode = None

                # Exact match in ngrams (score=2)
                if trigger_lower in nl_ngrams:
                    score = 2
                    match_mode = "exact"
                # Subset match: all trigger words present (score=1)
                elif trigger_words.issubset(task_tokens):
                    score = 1
                    match_mode = "subset"

                if score > 0:
                    candidates.append(
                        (
                            feature_id,
                            trigger,
                            score,
                            priority,
                            match_mode,
                            specificity,
                            support_terms_present,
                            support_terms_required,
                            is_single_word,
                        )
                    )

                    # Track single-word hits for guardrail
                    if is_single_word and priority >= 4:
                        single_word_hits.append(feature_id)

        # Single-word guardrail (T9.3.3)
        # Single-word triggers only allowed if:
        # (a) feature.priority >= 4
        # (b) AND no 2+ single-word triggers from different features present
        warning = None
        filtered_candidates = []

        for (
            feature_id,
            trigger,
            score,
            priority,
            match_mode,
            specificity,
            support_terms_present,
            support_terms_required,
            is_single_word,
        ) in candidates:
            if is_single_word and priority < 4:
                # Skip this candidate (fails guardrail)
                continue

            filtered_candidates.append(
                (
                    feature_id,
                    trigger,
                    score,
                    priority,
                    match_mode,
                    specificity,
                    support_terms_present,
                    support_terms_required,
                    is_single_word,
                )
            )

        # Find best candidate by (score, priority)
        if not filtered_candidates:
            return (
                None,
                None,
                None,
                0,
                None,
                {"blocked": False, "block_reason": "no_candidates", "top_k": []},
            )

        # Sort by (score desc, specificity desc, priority desc)
        filtered_candidates.sort(key=lambda x: (x[2], x[5], x[3]), reverse=True)

        single_word_feature_ids = {
            candidate[0] for candidate in filtered_candidates if candidate[8]
        }
        if len(single_word_feature_ids) > 1:
            non_single_word = [candidate for candidate in filtered_candidates if not candidate[8]]
            if non_single_word:
                filtered_candidates = non_single_word
            else:
                filtered_candidates.sort(key=lambda x: (x[2], x[5], x[3]), reverse=True)
                top_k = [
                    {
                        "feature_id": candidate[0],
                        "trigger": candidate[1],
                        "score": candidate[2],
                        "specificity": candidate[5],
                        "priority": candidate[3],
                    }
                    for candidate in filtered_candidates[:5]
                ]
                return (
                    None,
                    None,
                    "ambiguous_single_word_triggers",
                    0,
                    None,
                    {
                        "blocked": True,
                        "block_reason": "ambiguous_single_word_triggers",
                        "top_k": top_k,
                    },
                )

        best = filtered_candidates[0]
        (
            best_feature,
            best_trigger,
            best_score,
            best_priority,
            best_match_mode,
            best_specificity,
            best_support_terms_present,
            best_support_terms_required,
            best_is_single_word,
        ) = best

        # Check for ties in (score, specificity, priority)
        ties = [
            (fid, trig, score, spec, prio, mode)
            for fid, trig, score, prio, mode, spec, _, _, _ in filtered_candidates
            if score == best_score
            and spec == best_specificity
            and prio == best_priority
            and fid != best_feature
        ]

        if ties:
            # Tie detected → fallback with warning
            return (
                None,
                None,
                "match_tie_fallback",
                0,
                None,
                {
                    "blocked": True,
                    "block_reason": "match_tie_fallback",
                    "top_k": [
                        {
                            "feature_id": candidate[0],
                            "trigger": candidate[1],
                            "score": candidate[2],
                            "specificity": candidate[5],
                            "priority": candidate[3],
                        }
                        for candidate in filtered_candidates[:5]
                    ],
                },
            )

        if best_support_terms_required and not best_support_terms_present:
            return (
                None,
                None,
                "weak_single_word_trigger",
                0,
                None,
                {
                    "blocked": True,
                    "block_reason": "missing_support_term",
                    "support_terms_present": best_support_terms_present,
                    "support_terms_required": best_support_terms_required,
                    "weak_single_word_trigger": True,
                    "clamp_decision": "block",
                    "top_k": [
                        {
                            "feature_id": candidate[0],
                            "trigger": candidate[1],
                            "score": candidate[2],
                            "specificity": candidate[5],
                            "priority": candidate[3],
                        }
                        for candidate in filtered_candidates[:5]
                    ],
                },
            )

        return (
            best_feature,
            best_trigger,
            warning,
            best_score,
            best_match_mode,
            {
                "blocked": False,
                "score": best_score,
                "specificity": best_specificity,
                "priority": best_priority,
                "support_terms_present": best_support_terms_present,
                "support_terms_required": best_support_terms_required,
                "weak_single_word_trigger": False,
                "clamp_decision": "allow",
                "top_k": [
                    {
                        "feature_id": candidate[0],
                        "trigger": candidate[1],
                        "score": candidate[2],
                        "specificity": candidate[5],
                        "priority": candidate[3],
                    }
                    for candidate in filtered_candidates[:5]
                ],
            },
        )

    def _match_l3_alias(self, task: str, features: dict) -> tuple[str | None, int, str | None]:
        """L3: Alias match with structured triggers.

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
                _phrase_lower = phrase.lower()
                _phrase_tokens = self._tokenize(phrase)

                # Count matching terms
                matching_terms = sum(1 for t in terms if t.lower() in task_tokens)

                # High signal triggers auto-match if any term matches
                if high_signal and matching_terms >= 1:
                    if priority > best_priority or (
                        priority == best_priority and matching_terms > best_score
                    ):
                        best_match = feature_id
                        best_score = matching_terms
                        best_trigger_phrase = phrase
                        best_priority = priority
                    continue

                # Standard triggers require >= 2 term matches
                if matching_terms >= 2:
                    if priority > best_priority or (
                        priority == best_priority and matching_terms > best_score
                    ):
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
        entrypoints_match = re.search(r"### index\.entrypoints.*?\n\n(.*?)###", content, re.DOTALL)
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
            "selected_by": None,  # "feature" (L1) | "nl_trigger" (L2) | "alias" (L3) | "fallback" (L4)
            "match_terms_count": 0,
            "matched_trigger": None,
            "l2_warning": None,  # T9.3.3: L2 warnings
            "l2_score": 0,  # T9.3.3: L2 match score
            "l2_match_mode": None,  # T9.3.3: "exact" | "subset" | None
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

        # Normalize task for L2/L3 matching (T9.3.2)
        normalized_task = self._normalize_task(task)

        # === L1: Explicit feature id ===
        feature_id = self._match_l1_explicit_feature(task, available_features)

        if feature_id:
            result["selected_feature"] = feature_id
            result["plan_hit"] = True
            result["selected_by"] = "feature"
            result["budget_est"]["why"] = f"L1: Explicit feature:{feature_id}"
        else:
            # === L2: Direct NL trigger match (T9.3.3) ===
            (
                feature_id,
                nl_trigger,
                warning,
                score,
                match_mode,
                debug_info,
            ) = self._match_l2_nl_triggers(task, features)

            if feature_id:
                result["selected_feature"] = feature_id
                result["plan_hit"] = True
                result["selected_by"] = "nl_trigger"
                result["matched_trigger"] = nl_trigger
                result["l2_warning"] = warning
                result["l2_score"] = score
                result["l2_match_mode"] = match_mode
                result["l2_blocked"] = debug_info.get("blocked")
                result["l2_block_reason"] = debug_info.get("block_reason")
                result["l2_support_terms_required"] = debug_info.get(
                    "support_terms_required", False
                )
                result["l2_support_terms_present"] = debug_info.get("support_terms_present", [])
                result["l2_weak_single_word_trigger"] = debug_info.get(
                    "weak_single_word_trigger", False
                )
                result["l2_clamp_decision"] = debug_info.get("clamp_decision", "allow")
                result["budget_est"]["why"] = (
                    f"L2: NL trigger '{nl_trigger}' (score={score}, mode={match_mode})"
                )
            elif warning:
                # L2 matched but guardrail/tie caused fallback
                result["selected_by"] = "fallback"
                result["l2_warning"] = warning
                result["l2_blocked"] = debug_info.get("blocked")
                result["l2_block_reason"] = debug_info.get("block_reason")
                result["l2_support_terms_required"] = debug_info.get(
                    "support_terms_required", False
                )
                result["l2_support_terms_present"] = debug_info.get("support_terms_present", [])
                result["l2_weak_single_word_trigger"] = debug_info.get(
                    "weak_single_word_trigger", warning == "weak_single_word_trigger"
                )
                result["l2_clamp_decision"] = debug_info.get("clamp_decision", "block")
                result["budget_est"]["why"] = f"L4: L2 guardrail/tie ({warning}), using entrypoints"
            else:
                # === L3: Alias match (using normalized task) ===
                feature_id, match_score, trigger_phrase = self._match_l3_alias(
                    normalized_task, features
                )

                if feature_id:
                    result["selected_feature"] = feature_id
                    result["plan_hit"] = True
                    result["selected_by"] = "alias"
                    result["match_terms_count"] = match_score
                    result["matched_trigger"] = trigger_phrase
                    result["budget_est"]["why"] = (
                        f"L3: Alias match via '{trigger_phrase}' ({match_score} terms)"
                    )
                else:
                    # === L4: Fallback to entrypoints ===
                    result["selected_by"] = "fallback"
                    result["budget_est"]["why"] = "L4: No feature match, using entrypoints"

            if "l2_blocked" not in result:
                result["l2_blocked"] = debug_info.get("blocked")
            if "l2_block_reason" not in result:
                result["l2_block_reason"] = debug_info.get("block_reason")
            if "l2_support_terms_required" not in result:
                result["l2_support_terms_required"] = debug_info.get(
                    "support_terms_required", False
                )
            if "l2_support_terms_present" not in result:
                result["l2_support_terms_present"] = debug_info.get("support_terms_present", [])
            if "l2_weak_single_word_trigger" not in result:
                result["l2_weak_single_word_trigger"] = debug_info.get(
                    "weak_single_word_trigger", False
                )
            if "l2_clamp_decision" not in result:
                result["l2_clamp_decision"] = debug_info.get(
                    "clamp_decision", "block" if warning else "allow"
                )

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
                result["budget_est"]["why"] = (
                    f"L3: Bundle assertions failed for {failed_feature_id}, using entrypoints"
                )
            else:
                # Assertions passed - use the bundle
                result["bundle_assert_ok"] = True

                # Parse chunk IDs
                chunks_str = ", ".join(bundle["chunks"])
                result["chunk_ids"] = [
                    cid.strip() for cid in re.findall(r"`?([^:,`]+)`?", chunks_str)
                ]
                result["paths"] = bundle["paths"]

                # Generate next steps
                if any(kw in task.lower() for kw in ["implement", "add", "create"]):
                    result["next_steps"].append(
                        {
                            "action": "implement",
                            "target": result["paths"][0] if result["paths"] else ".",
                        }
                    )
                else:
                    result["next_steps"].append(
                        {"action": "read", "target": result["paths"][0] if result["paths"] else "."}
                    )

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
                    telemetry_attrs["bundle_assert_failed_paths"] = result.get(
                        "bundle_assert_failed_paths", []
                    )
                    telemetry_attrs["bundle_assert_failed_anchors"] = result.get(
                        "bundle_assert_failed_anchors", []
                    )

            # T9.3.3: Include L2 matching details
            if result.get("l2_warning"):
                telemetry_attrs["l2_warning"] = result["l2_warning"]
            if result.get("l2_score") > 0:
                telemetry_attrs["l2_score"] = result["l2_score"]
            if result.get("l2_match_mode"):
                telemetry_attrs["l2_match_mode"] = result["l2_match_mode"]
            if "l2_blocked" in result:
                telemetry_attrs["l2_blocked"] = result["l2_blocked"]
            if result.get("l2_block_reason"):
                telemetry_attrs["l2_block_reason"] = result["l2_block_reason"]
            if "l2_support_terms_required" in result:
                telemetry_attrs["l2_support_terms_required"] = result["l2_support_terms_required"]
                telemetry_attrs["support_terms_required"] = result["l2_support_terms_required"]
            if "l2_support_terms_present" in result:
                telemetry_attrs["l2_support_terms_present"] = result["l2_support_terms_present"]
                telemetry_attrs["support_terms_present"] = result["l2_support_terms_present"]
            if "l2_weak_single_word_trigger" in result:
                telemetry_attrs["l2_weak_single_word_trigger"] = result[
                    "l2_weak_single_word_trigger"
                ]
                telemetry_attrs["weak_single_word_trigger"] = result["l2_weak_single_word_trigger"]
            if "l2_clamp_decision" in result:
                telemetry_attrs["l2_clamp_decision"] = result["l2_clamp_decision"]
                telemetry_attrs["clamp_decision"] = result["l2_clamp_decision"]

            self.telemetry.event(
                "ctx.plan",
                {"task_hash": result["task_hash"]},
                telemetry_attrs,
                result["latency_ms"],
            )

        return result
