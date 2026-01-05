"""
PR#2 Telemetry Integration: Emit ast.*, selector.*, file.read, lsp.* events.

This module bridges AST/Selector/LSP operations with the PR#1 Telemetry layer.
All extras go under payload["x"] namespace.
"""

from pathlib import Path
from typing import Optional
import json

from src.infrastructure.telemetry import Telemetry
from src.application.ast_parser import SkeletonMapBuilder, ParseResult
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
        parse_result: ParseResult,
        parse_ms: int = 0,
    ) -> None:
        """
        Emit ast.parse event.

        Args:
            file_path: File being parsed (logged as relative path)
            parse_result: Resultado del parseo (ParseResult)
            parse_ms: Tiempo de parseo en milisegundos
        """
        # Calcular metadatos (NO incluir contenido crudo)
        symbols_count = len(parse_result.symbols)
        cache_key = parse_result.cache_key
        cache_status = parse_result.status
        
        # Calcular tamaño del skeleton usando to_dict()
        skeleton_bytes = len(json.dumps([s.to_dict() for s in parse_result.symbols]))

        # Emit event con metadatos seguros
        self.tel.event(
            cmd="ast.parse",
            args={"file": str(file_path)},
            result={
                "status": "ok",
                "symbols_count": symbols_count,
            },
            timing_ms=parse_ms,
            # Metadatos seguros (sin contenido crudo)
            file=str(file_path),
            cache_key=cache_key,
            cache_status=cache_status,
            symbols_count=symbols_count,
            skeleton_bytes=skeleton_bytes,
        )

        # Increment counters
        self.tel.incr("ast_parse_count", 1)
        if cache_status == "hit":
            self.tel.incr("ast_cache_hit_count", 1)
        elif cache_status == "miss":
            self.tel.incr("ast_cache_miss_count", 1)
        elif cache_status == "error":
            self.tel.incr("ast_cache_error_count", 1)


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
        # Build query string from SymbolQuery
        query_str = f"sym://python/{query.path}"
        if query.member:
            query_str += f"#{query.member}"
        
        self.tel.event(
            cmd="selector.resolve",
            args={"query": query_str},
            result={
                "status": "ok" if result.resolved else "not_resolved",
                "resolved": result.resolved,
            },
            timing_ms=0,  # Caller should measure
            # Extras under x
            symbol_query=query_str,
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
