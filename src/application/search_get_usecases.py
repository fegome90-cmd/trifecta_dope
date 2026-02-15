"""Use case wrappers for Search and Get with telemetry."""

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any, Literal, Optional

from src.application.context_service import ContextService, GetResult
from src.application.zero_hit_tracker import create_zero_hit_tracker
from src.application.spanish_aliases import detect_spanish, expand_with_spanish_aliases
from src.infrastructure.file_system import FileSystemAdapter
from src.domain.query_linter import LinterPlan


def _detect_source() -> str:
    """Detect execution source for telemetry segmentation.

    Returns:
        One of: 'test', 'fixture', 'interactive', 'agent'
    """
    # Check environment variable first (allows explicit override)
    env_source = os.environ.get("TRIFECTA_TELEMETRY_SOURCE")
    if env_source in ("test", "fixture", "interactive", "agent"):
        return env_source

    # Auto-detect based on Python environment
    import sys

    # Detect if running under pytest
    if "pytest" in sys.modules:
        return "test"

    # Detect if running in CI/automated environment
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return "fixture"

    # Detect if running in Claude Code / agent context
    if os.environ.get("CLAUDE_CODE") or os.environ.get("AGENT_CONTEXT"):
        return "agent"

    # Default to interactive
    return "interactive"


def _get_build_sha() -> str:
    """Get git commit SHA for build tracking.

    Returns:
        First 8 characters of git HEAD SHA, or 'unknown' if not in git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=True
        )
        return result.stdout.strip()[:8]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def _classify_zero_hit_reason(
    query: str, query_class: str, alias_expanded: bool, linter_expanded: bool
) -> str:
    """Classify why a search returned zero hits.

    Args:
        query: The search query
        query_class: Linter classification (vague|guided|semi|disabled)
        alias_expanded: Whether alias expansion was applied
        linter_expanded: Whether linter expansion was applied

    Returns:
        Reason code: 'empty'|'vague'|'no_alias'|'strict_filter'|'unknown'
    """
    # Empty or whitespace-only query
    if not query or not query.strip():
        return "empty"

    # Very short queries (1-2 chars) are likely vague
    if len(query.strip()) <= 2:
        return "vague"

    # Vague classification from linter
    if query_class == "vague":
        return "vague"

    # No expansion applied when it could have helped
    if not alias_expanded and not linter_expanded:
        # Query might need expansion but didn't get it
        if len(query.strip().split()) <= 2:
            return "no_alias"

    # Expansion applied but still no hits = strict filter
    if alias_expanded or linter_expanded:
        return "strict_filter"

    return "unknown"


class SearchUseCase:
    """Wrapper for ctx.search with telemetry."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(
        self, target_path: Path, query: str, limit: int = 5, enable_lint: bool = False
    ) -> str:
        """Execute search with query linting, alias expansion and format output.

        Pipeline:
        1. Normalize query (lowercase, strip, collapse whitespace)
        2. Linter (if enabled): classify + anchor expansion for vague queries
        3. Tokenize FINAL query (after linter decision) - CRITICAL ORDER
        4. Alias expansion (synonym-based via _ctx/aliases.yaml)
        5. Search: execute weighted search across all terms

        Args:
            target_path: Segment path to search
            query: Raw search query
            limit: Max results to return
            enable_lint: If True, apply query linter for anchor guidance (default: False)

        Returns:
            Formatted search results string
        """
        from src.infrastructure.alias_loader import AliasLoader
        from src.application.query_normalizer import QueryNormalizer
        from src.application.query_expander import QueryExpander
        from src.infrastructure.segment_utils import resolve_segment_root
        from src.infrastructure.config_loader import ConfigLoader
        from src.domain.query_linter import lint_query

        # B2 Intervention: Validate query early to prevent zero-hit searches
        is_valid, error_msg = QueryNormalizer.validate(query)
        if not is_valid:
            # Record telemetry for rejected query
            if self.telemetry:
                source = _detect_source()
                build_sha = _get_build_sha()
                self.telemetry.incr("ctx_search_rejected_invalid_query_count")
                self.telemetry.event(
                    "ctx.search.rejected",
                    {"query_preview": str(query)[:50], "reason": error_msg},
                    {"hits": 0, "rejected": True},
                    1,
                    source=source,
                    build_sha=build_sha,
                    rejection_reason=error_msg,
                )
            return f"❌ Query rejected: {error_msg}"

        # Load aliases
        alias_loader = AliasLoader(target_path)
        aliases = alias_loader.load()

        # Normalize query
        normalized_query = QueryNormalizer.normalize(query)

        # Apply Query Linter (anchor-based classification + expansion)
        lint_plan: LinterPlan
        if enable_lint:
            repo_root = resolve_segment_root(target_path)
            anchors_cfg = ConfigLoader.load_anchors(repo_root)
            aliases_cfg = ConfigLoader.load_linter_aliases(repo_root)

            lint_plan = lint_query(normalized_query, anchors_cfg, aliases_cfg)

            # If config missing, force disabled state
            if anchors_cfg.get("_missing_config") or aliases_cfg.get("_missing_config"):
                lint_plan["query_class"] = "disabled_missing_config"
                lint_plan["changed"] = False
                lint_plan["changes"] = {"added_strong": [], "added_weak": [], "reasons": []}
                query_for_expander = normalized_query
            else:
                query_for_expander = (
                    lint_plan["expanded_query"] if lint_plan["changed"] else normalized_query
                )
        else:
            lint_plan = {
                "original_query": normalized_query,
                "query_class": "disabled",
                "token_count": 0,
                "anchors_detected": {"strong": [], "weak": [], "aliases_matched": []},
                "expanded_query": normalized_query,
                "changed": False,
                "changes": {"added_strong": [], "added_weak": [], "reasons": []},
            }
            query_for_expander = normalized_query

        # CRITICAL: Tokenize AFTER linter decides final query
        tokens = QueryNormalizer.tokenize(query_for_expander)

        # Expand query with aliases
        expander = QueryExpander(aliases)
        expanded_terms = expander.expand(query_for_expander, tokens)

        # Execute search for each term and combine results
        service = ContextService(target_path)
        combined_results: dict[str, tuple[Any, float]] = {}  # chunk_id -> (hit, max_score)

        for term, weight in expanded_terms:
            result = service.search(term, k=limit * 2)  # Get more to allow for de-dupe
            for hit in result.hits:
                weighted_score = hit.score * weight
                if hit.id not in combined_results or weighted_score > combined_results[hit.id][1]:
                    combined_results[hit.id] = (hit, weighted_score)

        # Sort by weighted score and take top N
        sorted_hits = sorted(combined_results.values(), key=lambda x: x[1], reverse=True)[:limit]
        final_hits = [hit for hit, _ in sorted_hits]

        # Get expansion metadata for telemetry
        expansion_meta = expander.get_expansion_metadata(expanded_terms)

        # Sanitize query for telemetry (NEVER store raw query)
        query_preview = query[:200]  # Truncate preview
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]  # First 16 chars
        query_len = len(query)

        # Linter metadata
        linter_meta = {
            "linter_query_class": lint_plan["query_class"],
            "linter_expanded": lint_plan["changed"],
            "linter_added_strong_count": len(lint_plan["changes"]["added_strong"]),
            "linter_added_weak_count": len(lint_plan["changes"]["added_weak"]),
            "linter_reasons": lint_plan["changes"]["reasons"][:3],  # Max 3 reasons
        }

        # B0 Instrumentation: Source and build tracking
        source = _detect_source()
        build_sha = _get_build_sha()

        # Two-pass search: if zero-hit and Spanish detected, try aliases
        spanish_alias_applied = False
        spanish_alias_variants = []
        pass1_hits = len(final_hits)  # Track pass1 (before alias attempt)
        if len(final_hits) == 0 and source != "fixture":
            if detect_spanish(query):
                spanish_alias_variants = expand_with_spanish_aliases(normalized_query)
                for variant in spanish_alias_variants[1:]:
                    result = service.search(variant, k=limit * 2)
                    for hit in result.hits:
                        if hit.id not in combined_results:
                            combined_results[hit.id] = (hit, hit.score * 0.8)
                    if combined_results:
                        break

        pass2_hits = 0
        if combined_results and not final_hits:
            sorted_hits = sorted(combined_results.values(), key=lambda x: x[1], reverse=True)[
                :limit
            ]
            final_hits = [hit for hit, _ in sorted_hits]
            pass2_hits = len(final_hits)
            spanish_alias_applied = len(spanish_alias_variants) > 1 and pass2_hits > 0

        search_mode = (
            "with_expansion"
            if (expansion_meta["alias_expanded"] or lint_plan["changed"])
            else "search_only"
        )

        # B0 Instrumentation: Zero-hit reason classification
        zero_hit_reason = None
        if len(final_hits) == 0:
            zero_hit_reason = _classify_zero_hit_reason(
                query,
                lint_plan["query_class"],
                expansion_meta["alias_expanded"],
                lint_plan["changed"],
            )

        # Record telemetry
        if self.telemetry:
            self.telemetry.incr("ctx_search_count")
            self.telemetry.incr("ctx_search_hits_total", len(final_hits))
            self.telemetry.incr(f"ctx_search_by_source_{source}_count")

            # Spanish alias telemetry - only emit when alias recovered hits
            if spanish_alias_applied:
                self.telemetry.incr("ctx_search_spanish_alias_count")
                self.telemetry.event(
                    "ctx.search.spanish_alias",
                    {"query_preview": query_preview, "variants_tried": len(spanish_alias_variants)},
                    {
                        "pass1_hits": pass1_hits,
                        "pass2_hits": pass2_hits,
                        "recovered": pass2_hits > 0,
                    },
                    1,
                )

            if len(final_hits) == 0:
                self.telemetry.incr("ctx_search_zero_hits_count")
                if zero_hit_reason:
                    self.telemetry.incr(f"ctx_search_zero_hit_reason_{zero_hit_reason}_count")

                # ZeroHitTracker: record structured zero-hit event
                if self.telemetry and hasattr(self.telemetry, "_ctx_dir"):
                    try:
                        tracker = create_zero_hit_tracker(self.telemetry._ctx_dir)
                        tracker.record_zero_hit(
                            query=query,
                            segment_fingerprint=self.telemetry.segment_id,
                            segment_slug=self.telemetry.segment_label,
                            source=source,
                            build_sha=build_sha,
                            mode=search_mode,
                            zero_hit_reason=zero_hit_reason,
                            limit=limit,
                        )
                    except Exception:
                        pass  # Non-blocking: tracker should not break search

            # Linter metrics
            if lint_plan["changed"]:
                self.telemetry.incr("ctx_search_linter_expansion_count")
            self.telemetry.incr(f"ctx_search_linter_class_{lint_plan['query_class']}_count")

            # Alias expansion metrics
            if expansion_meta["alias_expanded"]:
                self.telemetry.incr("ctx_search_alias_expansion_count")
                self.telemetry.incr(
                    "ctx_search_alias_terms_total", expansion_meta["alias_terms_count"]
                )

            # Unified event with SANITIZED query and B0 instrumentation
            event_args = {
                "query_preview": query_preview,
                "query_hash": query_hash,
                "query_len": query_len,
                "limit": limit,
                **expansion_meta,
                **linter_meta,
            }

            # B0: Add segmentation tags to event
            event_result = {"hits": len(final_hits), "returned_ids": [h.id for h in final_hits]}

            # B0: Add extended fields via kwargs (goes into 'x' field per PR#1)
            event_kwargs = {
                "source": source,
                "build_sha": build_sha,
                "mode": search_mode,
            }

            if zero_hit_reason:
                event_kwargs["zero_hit_reason"] = zero_hit_reason

            self.telemetry.event(
                "ctx.search",
                event_args,
                event_result,
                1,  # timing_ms >= 1 required
                **event_kwargs,
            )

        # Format output
        if not final_hits:
            return f"No results found for query: '{query}'"

        output = [f"Search Results ({len(final_hits)} hits):\n"]
        for i, hit in enumerate(final_hits, 1):
            output.append(f"{i}. [{hit.id}] {hit.title_path[0]}")
            output.append(f"   Score: {hit.score:.2f} | Tokens: ~{hit.token_est}")
            output.append(f"   Preview: {hit.preview[:120]}...\n")

        return "\n".join(output)


class GetChunkUseCase:
    """Wrapper for ctx.get with telemetry."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def execute_with_result(
        self,
        target_path: Path,
        ids: list[str],
        mode: Literal["raw", "excerpt", "skeleton"] = "excerpt",
        budget_token_est: int = 1500,
        max_chunks: Optional[int] = None,
        stop_on_evidence: bool = False,
        query: Optional[str] = None,
    ) -> tuple[str, GetResult]:
        """Execute get and return both output and GetResult (for PD_REPORT)."""
        service = ContextService(target_path)
        result = service.get(
            ids,
            mode=mode,
            budget_token_est=budget_token_est,
            max_chunks=max_chunks,
            stop_on_evidence=stop_on_evidence,
            query=query,
        )

        # Record telemetry
        if self.telemetry:
            self.telemetry.incr("ctx_get_count")
            self.telemetry.incr("ctx_get_chunks_total", len(result.chunks))

            # Track mode usage
            mode_key = f"ctx_get_mode_{mode}_count"
            self.telemetry.incr(mode_key)

            # Check if budget was exceeded (trimming occurred)
            if result.total_tokens > budget_token_est:
                self.telemetry.incr("ctx_get_budget_trim_count")

            # Event with enhanced fields
            self.telemetry.event(
                "ctx.get",
                {
                    "ids": ids,
                    "mode": mode,
                    "budget": budget_token_est,
                    "max_chunks": max_chunks,
                    "stop_on_evidence": stop_on_evidence,
                },
                {
                    "chunks_returned": len(result.chunks),
                    "total_tokens": result.total_tokens,
                    "trimmed": result.total_tokens > budget_token_est,
                    "stop_reason": result.stop_reason,
                    "chunks_requested": result.chunks_requested,
                    "chars_returned_total": result.chars_returned_total,
                    "evidence": result.evidence_metadata,
                },
                1,  # timing_ms >= 1 required
            )

        # Format output
        output = [
            f"Retrieved {len(result.chunks)} chunk(s) (mode={mode}, tokens=~{result.total_tokens}):\n"
        ]

        for chunk in result.chunks:
            output.append(f"## [{chunk.id}] {' > '.join(chunk.title_path)}")
            output.append(chunk.text)
            output.append("")

        if result.total_tokens > budget_token_est:
            output.append("\n> [!WARNING]")
            output.append("> Budget exceeded. Some content may have been truncated.")

        return ("\n".join(output), result)

    def execute(
        self,
        target_path: Path,
        ids: list[str],
        mode: Literal["raw", "excerpt", "skeleton"] = "excerpt",
        budget_token_est: int = 1500,
        max_chunks: Optional[int] = None,
        stop_on_evidence: bool = False,
        query: Optional[str] = None,
    ) -> str:
        """Execute get and format output (API-compatible version)."""
        output, _ = self.execute_with_result(
            target_path, ids, mode, budget_token_est, max_chunks, stop_on_evidence, query
        )
        return output


class SyncContextUseCase:
    """Wrapper for ctx.sync (build + validate)."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(self, target_path: Path) -> str:
        """Execute sync (build + validate)."""
        from src.application.use_cases import BuildContextPackUseCase, ValidateContextPackUseCase

        # Build
        build_uc = BuildContextPackUseCase(self.file_system, self.telemetry)
        build_uc.execute(target_path)

        # Validate
        validate_uc = ValidateContextPackUseCase(self.file_system, self.telemetry)
        result = validate_uc.execute(target_path)

        if result.passed:
            return "✅ Context Pack synced and validated successfully."
        else:
            errors_str = "\n".join(f"  - {e}" for e in result.errors)
            return f"❌ Validation Failed:\n{errors_str}"
