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
from src.domain.result import Ok, Err, Result

_GRAPH_STALE_DAYS = 7
_GRAPH_TOTAL_BUDGET_MS = 15.0

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
        if hits:
            top_hit = hits[0]
            file_path = repo_path / top_hit.source_path
            if file_path.exists() and file_path.is_file():
                try:
                    ast_res = self.ast_builder.build(file_path)
                    ast_symbols = [s.name for s in ast_res.symbols]
                except Exception:
                    pass
        timings["ast_resolution_ms"] = int((time.time() - t0) * 1000)

        # 3. Graph Signal: Relational (NEW, conditional)
        graph_data: Optional[Dict[str, Any]] = None
        graph_signal = self._execute_graph_signal(repo_path, query, timings)
        if isinstance(graph_signal, dict):
            graph_data = graph_signal

        # 4. Deep Signal: LSP (Gated by state)
        t0 = time.time()
        lsp_data = None
        fidelity: Literal["full", "degraded", "fallback"] = "fallback"

        if self.lsp_client and hasattr(self.lsp_client, "state"):
            from src.infrastructure.lsp_client import LSPState
            if self.lsp_client.state == LSPState.READY:
                lsp_data = {"status": "available", "info": "Deep language analysis ready"}
                fidelity = "full"
            elif self.lsp_client.state == LSPState.WARMING:
                fidelity = "degraded"
            else:
                fidelity = "fallback"

        if fidelity == "fallback" and ast_symbols:
            fidelity = "degraded"
        timings["lsp_signal_ms"] = int((time.time() - t0) * 1000)

        latency_ms = int((time.time() - start_time) * 1000)

        metadata: Dict[str, Any] = {
            "latency_ms": latency_ms,
            "timings": timings,
            "query": query,
            "hit_count": len(hits),
            "ast_symbol_count": len(ast_symbols),
            "graph_signal": graph_signal if isinstance(graph_signal, str) else "used",
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
            self.telemetry.event(
                "ctx_oracle",
                args={"query": query, "fidelity": fidelity},
                result={"hit_count": len(hits), "fidelity": fidelity},
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

        # Use best match as resolved target
        best_match = search_nodes[0].get("symbol_name", target)

        # Gate 5: Budget check — traversal
        if _elapsed() > _GRAPH_TOTAL_BUDGET_MS:
            timings["graph_signal_ms"] = int(_elapsed())
            return "timeout"

        try:
            if relation == "callers":
                result = self.graph_service.callers(repo_path, best_match)
            else:
                result = self.graph_service.callees(repo_path, best_match)
        except Exception:
            timings["graph_signal_ms"] = int(_elapsed())
            return "unavailable"

        elapsed_total = _elapsed()
        timings["graph_signal_ms"] = int(elapsed_total)

        nodes = result.get("nodes", [])
        trimmed = [_trim_node(n) for n in nodes]

        # Return data even if slightly over budget — work already done
        return {
            "relation": relation,
            "target": best_match,
            "nodes": trimmed,
            "latency_ms": round(elapsed_total, 1),
            "over_budget": elapsed_total > _GRAPH_TOTAL_BUDGET_MS,
        }
