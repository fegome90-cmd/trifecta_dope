"""
Oracle Use Case - High-fidelity Signal Fusion (LSP + AST + PRIME + Graph).

Orchestrates multiple intelligence layers to provide a unified structural
and documentation context with automated fallback and fidelity reporting.
Signal order: PRIME → AST → Graph → LSP.
"""

import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from src.application.ast_parser import SkeletonMapBuilder
from src.application.context_service import ContextService
from src.domain.context_models import OracleResult, SearchHit
from src.domain.query_classifier import classify_query
from src.domain.segment_resolver import resolve_segment_ref
from src.domain.result import Ok, Err, Result

_GRAPH_STALE_DAYS = 7
_GRAPH_TOTAL_BUDGET_MS = 15.0
_LSP_BUDGET_MS = 20.0

_TRIMMED_NODE_KEYS = frozenset({"symbol_name", "qualified_name", "file_rel", "line", "kind"})


def _is_graph_fresh(status: Dict[str, Any]) -> bool:
    """Return True if graph was indexed within the last 7 days."""
    last = status.get("last_indexed_at")
    if not last:
        return False
    try:
        indexed_at = datetime.fromisoformat(last)
        if indexed_at.tzinfo is None:
            indexed_at = indexed_at.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=_GRAPH_STALE_DAYS)
        return indexed_at > cutoff
    except (ValueError, TypeError):
        return False


def _trim_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only the keys a consumer needs."""
    return {k: node[k] for k in _TRIMMED_NODE_KEYS if k in node}


class SearchOracleUseCase:
    """Orchestrator for unified intelligence retrieval."""

    def __init__(
        self,
        ast_builder: SkeletonMapBuilder,
        lsp_client: Optional[Any] = None,
        graph_service: Optional[Any] = None,
        telemetry: Optional[Any] = None,
    ):
        self.ast_builder = ast_builder
        self.lsp_client = lsp_client
        self.graph_service = graph_service
        self.telemetry = telemetry

    def execute(self, repo_path: Path, query: str, k: int = 5) -> Result[OracleResult, str]:
        """Execute unified search with signal fusion."""
        start_time = time.time()
        timings: Dict[str, Any] = {}

        # 1. Base Signal: PRIME Documentation
        t0 = time.time()
        try:
            svc = ContextService(repo_path)
            prime_res = svc.search(query, k=k)
            hits: List[SearchHit] = prime_res.hits
        except Exception as e:
            return Err(f"PRIME search failed: {str(e)}")
        timings["pack_load_and_search_ms"] = int((time.time() - t0) * 1000)

        # 2. Structural Signal: AST (Always available if file found)
        t0 = time.time()
        ast_symbols: List[str] = []
        ast_res: Optional[Any] = None
        ast_file_path: Optional[Path] = None
        if hits:
            top_hit = hits[0]
            file_path = repo_path / top_hit.source_path
            if file_path.exists() and file_path.is_file():
                try:
                    ast_res = self.ast_builder.build(file_path)
                    ast_symbols = [s.name for s in ast_res.symbols]
                    ast_file_path = file_path
                except Exception:
                    pass
        timings["ast_resolution_ms"] = int((time.time() - t0) * 1000)

        # 3. Graph Signal: Relational (conditional)
        graph_data: Optional[Dict[str, Any]] = None
        graph_signal = self._execute_graph_signal(repo_path, query, timings)
        if isinstance(graph_signal, dict):
            graph_data = graph_signal

        # 4. Deep Signal: LSP (Gated by predicate + state + budget)
        lsp_signal_result = self._execute_lsp_signal(
            repo_path, query, timings, ast_result=ast_res, file_path=ast_file_path,
        )
        if isinstance(lsp_signal_result, dict):
            lsp_data: Optional[Dict[str, Any]] = lsp_signal_result
            lsp_signal: str = "lsp_used"
        else:
            lsp_data = None
            lsp_signal = lsp_signal_result

        # 5. Fidelity determination
        if lsp_signal == "lsp_used":
            fidelity: Literal["full", "degraded", "fallback"] = "full"
        elif ast_symbols:
            fidelity = "degraded"
        else:
            fidelity = "fallback"

        latency_ms = int((time.time() - start_time) * 1000)

        metadata: Dict[str, Any] = {
            "latency_ms": latency_ms,
            "timings": timings,
            "query": query,
            "hit_count": len(hits),
            "ast_symbol_count": len(ast_symbols),
            "graph_signal": graph_signal if isinstance(graph_signal, str) else "used",
            "lsp_signal": lsp_signal,
        }

        result = OracleResult(
            fidelity=fidelity,
            lsp_data=lsp_data,
            ast_symbols=ast_symbols,
            prime_chunks=hits,
            graph_data=graph_data,
            metadata=metadata,
        )

        if self.telemetry:
            graph_signal_str = metadata.get("graph_signal", "unknown")
            self.telemetry.event(
                "ctx_oracle",
                args={"query": query, "fidelity": fidelity},
                result={
                    "hit_count": len(hits),
                    "fidelity": fidelity,
                    "graph_signal": graph_signal_str,
                    "graph_signal_ms": timings.get("graph_signal_ms", 0),
                    "lsp_signal": lsp_signal,
                    "lsp_signal_ms": timings.get("lsp_signal_ms", 0),
                    "ast_symbol_count": len(ast_symbols),
                },
                timing_ms=latency_ms,
                level="lite",
            )

        return Ok(result)

    def _execute_graph_signal(
        self,
        repo_path: Path,
        query: str,
        timings: Dict[str, Any],
    ) -> str | Dict[str, Any]:
        """Execute graph signal if query has relational predicate.

        Returns either a signal state string or a graph_data dict.
        Populates timings with graph-specific metrics.
        """
        # Gate 1: Detect predicate
        cls = classify_query(query)
        if cls.predicate is None:
            timings["graph_signal_ms"] = 0
            return "no_predicate"

        # Gate 2: Graph service available?
        if self.graph_service is None:
            timings["graph_signal_ms"] = 0
            return "unavailable"

        t_graph_start = time.time()

        def _elapsed() -> float:
            return (time.time() - t_graph_start) * 1000

        relation = cls.predicate.relation
        target = cls.predicate.target

        # Gate 3: Staleness check
        try:
            status = self.graph_service.status(repo_path)
        except Exception:
            timings["graph_signal_ms"] = int(_elapsed())
            return "unavailable"

        if not status.get("exists") or not _is_graph_fresh(status):
            timings["graph_signal_ms"] = int(_elapsed())
            return "stale"

        # Gate 4: Budget check — resolve target via fuzzy search
        if _elapsed() > _GRAPH_TOTAL_BUDGET_MS:
            timings["graph_signal_ms"] = int(_elapsed())
            return "timeout"

        try:
            search_result = self.graph_service.search(repo_path, target, limit=5)
        except Exception:
            timings["graph_signal_ms"] = int(_elapsed())
            return "unavailable"

        search_nodes = search_result.get("nodes", [])
        if not search_nodes:
            timings["graph_signal_ms"] = int(_elapsed())
            return "target_not_found"

        # Disambiguate: prefer first fuzzy match (has file_rel context)
        best = search_nodes[0]
        resolved_name = best.get("symbol_name", target)
        resolved_file = best.get("file_rel", "")

        # Gate 5: Budget check — traversal
        if _elapsed() > _GRAPH_TOTAL_BUDGET_MS:
            timings["graph_signal_ms"] = int(_elapsed())
            return "timeout"

        try:
            if relation == "callers":
                result = self.graph_service.callers(repo_path, resolved_name)
            else:
                result = self.graph_service.callees(repo_path, resolved_name)
        except Exception as exc:
            # Ambiguous target: symbol exists in multiple files
            exc_type = type(exc).__name__
            if exc_type == "AmbiguousGraphTargetError":
                # Disambiguate: build a qualified node ID from fuzzy search context
                # and query callers/callees for that specific node
                try:
                    segment_ref = resolve_segment_ref(repo_path)
                    qualified_id = f"{segment_ref.id}:{resolved_file}:{resolved_name}"
                    result = self._query_related_for_node_id(
                        repo_path, qualified_id, relation
                    )
                except Exception:
                    timings["graph_signal_ms"] = int(_elapsed())
                    return "ambiguous_target"
            else:
                timings["graph_signal_ms"] = int(_elapsed())
                return "unavailable"

        elapsed_total = _elapsed()
        timings["graph_signal_ms"] = int(elapsed_total)

        nodes = result.get("nodes", [])
        trimmed = [_trim_node(n) for n in nodes]

        # Return data even if slightly over budget — work already done
        return {
            "relation": relation,
            "target": resolved_name,
            "nodes": trimmed,
            "latency_ms": round(elapsed_total, 1),
            "over_budget": elapsed_total > _GRAPH_TOTAL_BUDGET_MS,
        }

    def _execute_lsp_signal(
        self,
        repo_path: Path,
        query: str,
        timings: Dict[str, Any],
        ast_result: Optional[Any] = None,
        file_path: Optional[Path] = None,
    ) -> str | Dict[str, Any]:
        """Execute LSP signal if query has semantic predicate.

        Returns either a signal state string or an lsp_data dict.
        Populates timings with lsp-specific metrics.
        """
        # Gate A: Detect semantic predicate
        cls = classify_query(query)
        if cls.semantic is None:
            timings["lsp_signal_ms"] = 0
            return "lsp_not_applicable"

        # Gate B: LSP client injected?
        if self.lsp_client is None:
            timings["lsp_signal_ms"] = 0
            return "lsp_not_injected"

        # Gate C: LSP client ready?
        from src.infrastructure.lsp_client import LSPState

        if self.lsp_client.state != LSPState.READY:
            timings["lsp_signal_ms"] = 0
            return "lsp_not_ready"

        # Gate D: Resolve symbol position from AST
        target = cls.semantic.target
        resolved_symbol = None
        if ast_result is not None and hasattr(ast_result, "symbols"):
            for sym in ast_result.symbols:
                if sym.name == target:
                    resolved_symbol = sym
                    break

        if resolved_symbol is None or file_path is None:
            timings["lsp_signal_ms"] = 0
            return "lsp_no_result"

        t_lsp_start = time.time()

        def _elapsed() -> float:
            return (time.time() - t_lsp_start) * 1000

        # Execute hover request
        file_uri = file_path.as_uri()
        line = resolved_symbol.start_line
        result = self.lsp_client.request(
            "textDocument/hover",
            {
                "textDocument": {"uri": file_uri},
                "position": {"line": line - 1, "character": 0},  # LSP uses 0-based lines
            },
        )

        elapsed = _elapsed()
        timings["lsp_signal_ms"] = int(elapsed)

        # Gate E: Budget check — AFTER request to detect slow LSP
        if elapsed > _LSP_BUDGET_MS:
            return "lsp_timeout"

        # Handle error response
        if result is None:
            return "lsp_no_result"

        if isinstance(result, dict) and result.get("__lsp_error__"):
            return "lsp_error"

        # Handle empty contents
        contents = result.get("contents")
        if contents is None or contents == "":
            return "lsp_no_result"

        file_rel = str(file_path.relative_to(repo_path)) if file_path.is_relative_to(repo_path) else str(file_path)

        return {
            "method": "hover",
            "target": resolved_symbol.name,
            "contents": contents,
            "latency_ms": round(elapsed, 1),
            "source_file": file_rel,
            "source_line": line,
        }

    def _query_related_for_node_id(
        self,
        repo_path: Path,
        node_id: str,
        relation: str,
    ) -> Dict[str, Any]:
        """Query callers/callees for a specific node ID, bypassing symbol resolution."""
        from src.infrastructure.graph_store import GraphStore

        segment_ref = resolve_segment_ref(repo_path)
        db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)
        store = GraphStore.open_readonly(
            db_path, segment_ref.id,
            required_tables=GraphStore.RELATION_REQUIRED_TABLES,
        )
        reverse = relation == "callers"
        nodes = store.get_callers_for_node(segment_ref.id, node_id) if reverse else store.get_callees_for_node(segment_ref.id, node_id)
        return {
            "status": "ok",
            "segment_id": segment_ref.id,
            "symbol": node_id.split(":")[-1],
            "nodes": [n.to_dict() for n in nodes],
        }
