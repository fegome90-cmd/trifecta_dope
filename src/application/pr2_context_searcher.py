"""
PR#2 Façade: Unified interface for AST skeleton + selector + LSP + telemetry.

This is the main entry point for CLI integration (ctx.search, ctx.get).
"""

import threading
from pathlib import Path
from time import perf_counter_ns
from typing import Optional, TYPE_CHECKING

from src.infrastructure.telemetry import Telemetry
from src.application.ast_parser import SkeletonMapBuilder
from src.application.symbol_selector import SymbolQuery, SymbolResolver
from src.application.lsp_manager import LSPManager
from src.application.telemetry_pr2 import (
    ASTTelemetry,
    SelectorTelemetry,
    FileTelemetry,
    LSPTelemetry,
)

if TYPE_CHECKING:
    from src.domain.ast_cache import AstCache

__all__ = ["PR2ContextSearcher"]


class PR2ContextSearcher:
    """
    Unified context searcher: AST skeleton → selector → progressive disclosure + optional LSP.

    FLOW:
    1. Build AST skeleton from file(s)
    2. Use selector to find symbol by qualified name
    3. Read excerpt/raw based on disclosure mode
    4. Optionally warm-up LSP in parallel
    5. Return results with telemetry
    """

    def __init__(
        self,
        workspace_root: Path,
        tel: Telemetry,
        lsp_enabled: bool = False,
        cache: Optional["AstCache"] = None,
    ) -> None:
        """
        Initialize searcher.

        Args:
            workspace_root: Root directory of workspace
            tel: Telemetry instance (from PR#1)
            lsp_enabled: If True, spawn Pyright LSP in background
            cache: Instancia de AstCache (opcional, usa InMemoryLRUCache por defecto)
        """
        self.workspace_root = workspace_root
        self.tel = tel

        # Initialize cache (DI)
        if cache is None:
            # P1 Wiring: Use factory to respect env vars (TRIFECTA_AST_PERSIST)
            from src.infrastructure.factories import get_ast_cache

            cache = get_ast_cache(segment_id=str(workspace_root))
        self.cache = cache

        # Initialize components
        self.ast_builder = SkeletonMapBuilder(cache=self.cache, segment_id=str(workspace_root))
        self.selector = SymbolResolver(self.ast_builder)
        self.lsp_manager = LSPManager(workspace_root, enabled=lsp_enabled)

        # Telemetry wrappers
        self.ast_tel = ASTTelemetry(tel)
        self.selector_tel = SelectorTelemetry(tel)
        self.file_tel = FileTelemetry(tel)
        self.lsp_tel = LSPTelemetry(tel)

        # Track bytes read in this session
        self.total_bytes_read = 0

    def search_symbol(
        self,
        query_str: str,
        file_path: Optional[Path] = None,
        disclosure_mode: str = "skeleton",
    ) -> Optional[dict[str, object]]:
        """
        Search for symbol using sym:// DSL.

        FLOW:
        1. Parse sym://python/<qualified_name>
        2. If file provided: extract AST skeleton, resolve symbol
        3. Based on disclosure_mode: return skeleton only OR excerpt/raw
        4. Warm-up LSP in parallel (non-blocking)
        5. Emit telemetry events

        Args:
            query_str: sym://python/MyClass.method
            file_path: Optional file to search within
            disclosure_mode: "skeleton" | "excerpt" | "raw"

        Returns:
            Dict with symbol location + content OR None if not found
        """
        t_start = perf_counter_ns()

        # Parse query - returns Result[SymbolQuery, ASTError]
        from src.domain.result import Err

        query_result = SymbolQuery.parse(query_str)
        if isinstance(query_result, Err):
            return None
        query = query_result.value

        # If file provided: extract skeleton
        if file_path:
            self._extract_skeleton(file_path)

        # Resolve symbol - returns Result[Candidate, ASTError]
        resolve_result = self.selector.resolve(query)

        # Handle Result pattern for resolve
        if isinstance(resolve_result, Err):
            return None

        candidate = resolve_result.value

        # Convert Candidate to SymbolResolveResult for telemetry
        from src.application.symbol_selector import SymbolResolveResult

        result = SymbolResolveResult(
            resolved=True,
            file=candidate.file_rel,
            start_line=candidate.start_line,
            end_line=candidate.end_line,
        )
        self.selector_tel.track_resolve(query, result)

        if not hasattr(candidate, "file_rel") or not candidate.file_rel:
            return None

        # Get file and range from candidate
        resolved_file = candidate.file_rel

        start_line = candidate.start_line or 0
        end_line = candidate.end_line or start_line

        # Progressive disclosure: return based on mode
        output = {
            "file": resolved_file,
            "start_line": start_line,
            "end_line": end_line,
        }  # type: dict[str, object]

        if disclosure_mode in ("excerpt", "raw"):
            content = self._read_file_content(Path(resolved_file))
            if content:
                lines = content.split("\n")
                if disclosure_mode == "excerpt":
                    # Return ±5 lines around the symbol
                    excerpt_start = max(0, start_line - 5)
                    excerpt_end = min(len(lines), end_line + 5)
                    excerpt = "\n".join(lines[excerpt_start:excerpt_end])
                    output["excerpt"] = excerpt
                    output["excerpt_start_line"] = excerpt_start
                else:  # raw
                    output["content"] = content

        # Warm-up LSP in parallel (non-blocking)
        if self.lsp_manager.enabled:
            self._warmup_lsp_async(resolved_file, start_line)

        # Emit final telemetry
        t_end = perf_counter_ns()
        timing_ms = (t_end - t_start) // 1_000_000

        self.tel.event(
            cmd="search.symbol.end",
            args={"query": query_str},
            result={"status": "found" if result.resolved else "not_found"},
            timing_ms=timing_ms,
            bytes_read=self.total_bytes_read,
            disclosure_mode=disclosure_mode,
        )

        return output

    def _extract_skeleton(self, file_path: Path) -> None:
        """Extract AST skeleton from file and register with selector."""
        if not file_path.exists():
            return

        t_start = perf_counter_ns()

        try:
            content = file_path.read_text()
            parse_result = self.ast_builder.build(file_path, content)

            # Emit telemetry
            t_end = perf_counter_ns()
            timing_ms = (t_end - t_start) // 1_000_000

            self.ast_tel.track_parse(file_path, parse_result, parse_ms=timing_ms)
            self.tel.observe("ast.parse", timing_ms)

        except Exception:
            pass

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with bytes tracking."""
        try:
            content = file_path.read_text()
            bytes_read = len(content.encode())
            self.total_bytes_read += bytes_read

            # Emit file.read telemetry
            self.file_tel.track_read(file_path, "raw", bytes_read)

            return content
        except Exception:
            return None

    def _warmup_lsp_async(self, file_uri: str, start_line: int) -> None:
        """Spawn LSP warm-up in background (non-blocking)."""

        def _warmup_task() -> None:
            try:
                self.lsp_manager.spawn_async(file_uri)
            except Exception:
                pass

        t = threading.Thread(target=_warmup_task, daemon=True)
        t.start()

    def request_definition(
        self,
        file_uri: str,
        line: int,
        col: int,
    ) -> Optional[dict[str, object]]:
        """
        Request LSP definition (READY-only gating).

        Returns None and emits lsp.fallback if not READY.
        """
        t_start = perf_counter_ns()

        if self.lsp_manager.is_ready():
            result: Optional[dict[str, object]] = self.lsp_manager.request_definition(
                file_uri, line, col
            )
            t_end = perf_counter_ns()
            timing_ms = (t_end - t_start) // 1_000_000
            self.lsp_tel.track_request(
                "textDocument/definition",
                file_uri,
                line,
                col,
                resolved=result is not None,
                timing_ms=timing_ms,
            )
            return result
        else:
            self.lsp_tel.track_fallback(reason="lsp_not_ready")
            return None

    def shutdown(self) -> None:
        """Gracefully shutdown LSP."""
        self.lsp_manager.shutdown()
