"""Use case wrappers for Search and Get with telemetry."""

from pathlib import Path
from typing import Literal, Optional

from src.application.context_service import ContextService
from src.infrastructure.file_system import FileSystemAdapter


class SearchUseCase:
    """Wrapper for ctx.search with telemetry."""

    def __init__(self, file_system: FileSystemAdapter, telemetry=None):
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(self, target_path: Path, query: str, limit: int = 5) -> str:
        """Execute search with alias expansion and format output."""
        from src.infrastructure.alias_loader import AliasLoader
        from src.application.query_normalizer import QueryNormalizer
        from src.application.query_expander import QueryExpander
        
        # Load aliases
        alias_loader = AliasLoader(target_path)
        aliases = alias_loader.load()
        
        # Normalize query
        normalized_query = QueryNormalizer.normalize(query)
        tokens = QueryNormalizer.tokenize(normalized_query)
        
        # Expand query with aliases
        expander = QueryExpander(aliases)
        expanded_terms = expander.expand(normalized_query, tokens)
        
        # Execute search for each term and combine results
        service = ContextService(target_path)
        combined_results = {}  # chunk_id -> (hit, max_score)
        
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
        
        # Record telemetry
        if self.telemetry:
            self.telemetry.incr("ctx_search_count")
            self.telemetry.incr("ctx_search_hits_total", len(final_hits))
            if len(final_hits) == 0:
                self.telemetry.incr("ctx_search_zero_hits_count")
            
            if expansion_meta["alias_expanded"]:
                self.telemetry.incr("ctx_search_alias_expansion_count")
                self.telemetry.incr("ctx_search_alias_terms_total", expansion_meta["alias_terms_count"])
            
            # Event with details
            self.telemetry.event(
                "ctx.search",
                {
                    "query": query,
                    "limit": limit,
                    **expansion_meta
                },
                {"hits": len(final_hits), "returned_ids": [h.id for h in final_hits]},
                0,  # Timing handled in CLI
                []
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

    def __init__(self, file_system: FileSystemAdapter, telemetry=None):
        self.file_system = file_system
        self.telemetry = telemetry

    def execute(
        self,
        target_path: Path,
        ids: list[str],
        mode: Literal["raw", "excerpt", "skeleton"] = "excerpt",
        budget_token_est: int = 1500
    ) -> str:
        """Execute get and format output."""
        service = ContextService(target_path)
        result = service.get(ids, mode=mode, budget_token_est=budget_token_est)
        
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
            
            # Event
            self.telemetry.event(
                "ctx.get",
                {"ids": ids, "mode": mode, "budget": budget_token_est},
                {
                    "chunks_returned": len(result.chunks),
                    "total_tokens": result.total_tokens,
                    "trimmed": result.total_tokens > budget_token_est
                },
                0,
                []
            )
        
        # Format output
        output = [f"Retrieved {len(result.chunks)} chunk(s) (mode={mode}, tokens=~{result.total_tokens}):\n"]
        
        for chunk in result.chunks:
            output.append(f"## [{chunk.id}] {' > '.join(chunk.title_path)}")
            output.append(chunk.text)
            output.append("")
        
        if result.total_tokens > budget_token_est:
            output.append("\n> [!WARNING]")
            output.append("> Budget exceeded. Some content may have been truncated.")
        
        return "\n".join(output)


class SyncContextUseCase:
    """Wrapper for ctx.sync (build + validate)."""
    
    def __init__(self, file_system: FileSystemAdapter, telemetry=None):
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
