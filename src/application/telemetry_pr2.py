"""
PR#2 Telemetry Integration: Emit ast.*, selector.*, file.read, lsp.* events.

This module bridges AST/Selector/LSP operations with the PR#1 Telemetry layer.
All extras go under payload["x"] namespace.
"""

from pathlib import Path
from typing import Optional

from src.infrastructure.telemetry import Telemetry
from src.application.ast_parser import SkeletonMapBuilder, SymbolInfo
from src.application.symbol_selector import SymbolQuery, SymbolResolveResult
from src.application.lsp_manager import LSPState

__all__ = [
    "ASTTelemetry",
    "SelectorTelemetry",
    "FileTelemetry",
    "LSPTelemetry",
]


class ASTTelemetry:
    """Wrap AST operations with telemetry."""

    def __init__(self, tel: Telemetry) -> None:
        """Initialize with telemetry instance."""
        self.tel = tel
        self.ast_counter = SkeletonMapBuilder()

    def track_parse(
        self,
        file_path: Path,
        content: str,
        symbols: list[SymbolInfo],
        cache_hit: bool,
    ) -> None:
        """
        Emit ast.parse event.

        Args:
            file_path: File being parsed (logged as relative path)
            content: Source code
            symbols: Extracted symbols
            cache_hit: True if from cache
        """
        import hashlib

        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        skeleton_bytes = self.ast_counter.get_skeleton_bytes(symbols)

        # Emit event with extras under x
        self.tel.event(
            cmd="ast.parse",
            args={"file": str(file_path)},
            result={
                "status": "ok",
                "symbols_count": len(symbols),
            },
            timing_ms=0,  # Caller should measure actual timing
            # Extras under x namespace
            file=str(file_path),
            content_sha8=content_hash,
            skeleton_bytes=skeleton_bytes,
            cache_hit=cache_hit,
        )

        # Increment counters
        self.tel.incr("ast_parse_count", 1)
        if cache_hit:
            self.tel.incr("ast_cache_hit_count", 1)
        else:
            self.tel.incr("ast_cache_miss_count", 1)


class SelectorTelemetry:
    """Wrap selector resolution with telemetry."""

    def __init__(self, tel: Telemetry) -> None:
        """Initialize with telemetry instance."""
        self.tel = tel

    def track_resolve(
        self,
        query: SymbolQuery,
        result: SymbolResolveResult,
    ) -> None:
        """
        Emit selector.resolve event.

        Args:
            query: Parsed sym:// query
            result: Resolution result
        """
        self.tel.event(
            cmd="selector.resolve",
            args={"query": query.raw},
            result={
                "status": "ok" if result.resolved else "not_resolved",
                "resolved": result.resolved,
            },
            timing_ms=0,  # Caller should measure
            # Extras under x
            symbol_query=query.qualified_name,
            resolved=result.resolved,
            matches=result.matches,
            ambiguous=result.ambiguous,
        )


class FileTelemetry:
    """Track file reads with bytes_read_* counters."""

    def __init__(self, tel: Telemetry) -> None:
        """Initialize with telemetry instance."""
        self.tel = tel

    def track_read(
        self,
        file_path: Path,
        mode: str,
        bytes_read: int,
        status: str = "ok",
    ) -> None:
        """
        Emit file.read event and increment bytes counter.

        Args:
            file_path: File read (logged as relative path)
            mode: "skeleton" | "excerpt" | "raw"
            bytes_read: Number of bytes read
            status: "ok" or "error"
        """
        self.tel.event(
            cmd="file.read",
            args={"file": str(file_path), "mode": mode},
            result={"status": status},
            timing_ms=0,
            # Extras
            file=str(file_path),
            mode=mode,
            bytes=bytes_read,
        )

        # Increment counter: file_read_{mode}_bytes_total
        counter_name = f"file_read_{mode}_bytes_total"
        self.tel.incr(counter_name, bytes_read)


class LSPTelemetry:
    """Track LSP operations with telemetry."""

    def __init__(self, tel: Telemetry) -> None:
        """Initialize with telemetry instance."""
        self.tel = tel

    def track_spawn(self, pid: Optional[int] = None) -> None:
        """Emit lsp.spawn event."""
        self.tel.event(
            cmd="lsp.spawn",
            args={"server": "pyright"},
            result={"status": "spawned"},
            timing_ms=0,
            # Extras
            state="warming",
            server="pyright",
            pid=pid,
        )
        self.tel.incr("lsp_spawn_count", 1)

    def track_state_change(
        self,
        from_state: LSPState,
        to_state: LSPState,
        reason: str = "",
    ) -> None:
        """Emit lsp.state_change event."""
        self.tel.event(
            cmd="lsp.state_change",
            args={},
            result={"status": "ok"},
            timing_ms=0,
            # Extras
            from_state=from_state.value,
            to_state=to_state.value,
            reason=reason,
        )

        if to_state == LSPState.READY:
            self.tel.incr("lsp_ready_count", 1)
        elif to_state == LSPState.FAILED:
            self.tel.incr("lsp_failed_count", 1)

    def track_request(
        self,
        method: str,
        uri: str,
        line: int,
        col: int,
        resolved: bool,
        fallback: bool = False,
        timing_ms: int = 0,
    ) -> None:
        """Emit lsp.request event."""
        self.tel.event(
            cmd=f"lsp.{method.replace('/', '_').lower()}",
            args={"uri": uri, "line": line, "col": col},
            result={
                "status": "resolved" if resolved else "fallback",
            },
            timing_ms=timing_ms,
            # Extras
            method=method,
            file=uri,
            line=line,
            col=col,
            resolved=resolved,
            fallback=fallback,
        )

        if fallback:
            self.tel.incr("lsp_fallback_count", 1)

    def track_fallback(self, reason: str = "") -> None:
        """Emit lsp.fallback event when LSP not ready."""
        self.tel.event(
            cmd="lsp.fallback",
            args={},
            result={"status": "fallback_to_ast"},
            timing_ms=0,
            # Extras
            reason=reason or "lsp_not_ready",
            fallback_to="ast_only",
        )
        self.tel.incr("lsp_fallback_count", 1)
