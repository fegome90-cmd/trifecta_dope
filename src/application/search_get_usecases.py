"""Use case wrappers for Search and Get with telemetry."""

import hashlib
from pathlib import Path
from typing import Any, Literal, Optional

from src.application.context_service import ContextService, GetResult
from src.infrastructure.file_system import FileSystemAdapter


class SearchUseCase:
    """Wrapper for ctx.search with telemetry."""

    def __init__(self, file_system: FileSystemAdapter, telemetry: Any = None) -> None:
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(self, target_path: Path, query: str, limit: int = 5, enable_lint: bool = False) -> str:
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

        # Load aliases
        alias_loader = AliasLoader(target_path)
        aliases = alias_loader.load()

        # Normalize query
        normalized_query = QueryNormalizer.normalize(query)

        # Apply Query Linter (anchor-based classification + expansion)
        if enable_lint:
            repo_root = resolve_segment_root(target_path)
            anchors_cfg = ConfigLoader.load_anchors(repo_root)
            aliases_cfg = ConfigLoader.load_linter_aliases(repo_root)

            lint_plan = lint_query(normalized_query, anchors_cfg, aliases_cfg)

            # If config missing, force disabled state
            if anchors_cfg.get("_missing_config") or aliases_cfg.get("_missing_config"):
                lint_plan["query_class"] = "disabled_missing_config"
                lint_plan["changed"] = False
                query_for_expander = normalized_query
            else:
                query_for_expander = lint_plan["expanded_query"] if lint_plan["changed"] else normalized_query
        else:
            lint_plan = {
                "query_class": "disabled",
                "changed": False,
                "changes": {"added_strong": [], "added_weak": [], "reasons": []}
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
            "linter_added_strong_count": len(lint_plan.get("changes", {}).get("added_strong", [])),
            "linter_added_weak_count": len(lint_plan.get("changes", {}).get("added_weak", [])),
            "linter_reasons": lint_plan.get("changes", {}).get("reasons", [])[:3],  # Max 3 reasons
        }

        # Record telemetry
        if self.telemetry:
            self.telemetry.incr("ctx_search_count")
            self.telemetry.incr("ctx_search_hits_total", len(final_hits))
            if len(final_hits) == 0:
                self.telemetry.incr("ctx_search_zero_hits_count")

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

            # Unified event with SANITIZED query and linter metadata
            self.telemetry.event(
                "ctx.search",
                {
                    "query_preview": query_preview,
                    "query_hash": query_hash,
                    "query_len": query_len,
                    "limit": limit,
                    **expansion_meta,
                    **linter_meta,
                },
                {"hits": len(final_hits), "returned_ids": [h.id for h in final_hits]},
                1,  # timing_ms >= 1 required
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
