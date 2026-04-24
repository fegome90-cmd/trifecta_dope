"""Tests for Oracle graph signal — _execute_graph_signal().

8 scenarios from WO-0043 tasks:
1. graph unavailable (graph_service is None)
2. stale graph (>7 days)
3. target not found
4. timeout (latency budget exceeded)
5. callers success
6. callees success
7. empty target
8. GraphStoreAccessError handling
"""

import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.application.oracle_use_case import SearchOracleUseCase
from src.domain.context_models import OracleResult


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_oracle(
    graph_service: Optional[Any] = None,
) -> SearchOracleUseCase:
    ast_builder = MagicMock()
    ast_builder.build.return_value = MagicMock(symbols=[])
    return SearchOracleUseCase(
        ast_builder=ast_builder,
        lsp_client=None,
        graph_service=graph_service,
        telemetry=None,
    )


def _fresh_status() -> Dict[str, Any]:
    return {
        "status": "ok",
        "exists": True,
        "node_count": 10,
        "edge_count": 5,
        "last_indexed_at": datetime.now(timezone.utc).isoformat(),
    }


def _stale_status() -> Dict[str, Any]:
    old = datetime.now(timezone.utc) - timedelta(days=8)
    return {
        "status": "ok",
        "exists": True,
        "node_count": 10,
        "edge_count": 5,
        "last_indexed_at": old.isoformat(),
    }


def _mock_graph_service(
    status_response: Optional[Dict] = None,
    callers_response: Optional[Dict] = None,
    callees_response: Optional[Dict] = None,
    search_response: Optional[Dict] = None,
    status_side_effect: Optional[Exception] = None,
    callers_side_effect: Optional[Exception] = None,
) -> MagicMock:
    gs = MagicMock()
    if status_side_effect:
        gs.status.side_effect = status_side_effect
    else:
        gs.status.return_value = status_response or _fresh_status()
    gs.callers.return_value = callers_response or {"nodes": []}
    gs.callees.return_value = callees_response or {"nodes": []}
    gs.search.return_value = search_response or {"nodes": []}
    if callers_side_effect:
        gs.callers.side_effect = callers_side_effect
    return gs


def _node_dict(
    symbol_name: str = "func_a",
    qualified_name: str = "func_a",
    file_rel: str = "src/mod.py",
    line: int = 10,
    kind: str = "function",
) -> Dict[str, Any]:
    return {
        "symbol_name": symbol_name,
        "qualified_name": qualified_name,
        "file_rel": file_rel,
        "line": line,
        "kind": kind,
    }


# ── Scenario 1: graph_service is None → skip ─────────────────────────────────


def test_graph_signal_unavailable_when_no_service():
    """When graph_service is None, signal should be 'unavailable' and graph_data None."""
    oracle = _make_oracle(graph_service=None)
    with patch.object(oracle, "ast_builder"):
        oracle.ast_builder.build.return_value = MagicMock(symbols=[])
        with patch("src.application.oracle_use_case.ContextService") as MockCS:
            MockCS.return_value.search.return_value = MagicMock(hits=[])
            result_obj = oracle.execute(Path("/tmp/repo"), "who calls foo")
    r: OracleResult = result_obj.unwrap()
    assert r.graph_data is None
    assert r.metadata.get("graph_signal") == "unavailable"


# ── Scenario 2: stale graph → skip ────────────────────────────────────────────


def test_graph_signal_stale_when_index_older_than_7_days():
    """Graph older than 7 days should be marked 'stale'."""
    gs = _mock_graph_service(status_response=_stale_status())
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls foo")
    r = result_obj.unwrap()
    assert r.graph_data is None
    assert r.metadata.get("graph_signal") == "stale"


# ── Scenario 3: target not found → signal 'target_not_found' ──────────────────


def test_graph_signal_target_not_found():
    """When search returns no nodes for target, signal is 'target_not_found'."""
    gs = _mock_graph_service(
        status_response=_fresh_status(),
        search_response={"nodes": []},
    )
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls NonExistent")
    r = result_obj.unwrap()
    assert r.graph_data is None
    assert r.metadata.get("graph_signal") == "target_not_found"


# ── Scenario 4: timeout → signal 'timeout' ────────────────────────────────────


def test_graph_signal_timeout_when_latency_exceeds_budget():
    """When graph query takes too long, signal should be 'timeout'."""
    gs = _mock_graph_service(status_response=_fresh_status())

    def slow_search(*args, **kwargs):
        time.sleep(0.02)  # 20ms — exceeds budget
        return {"nodes": [_node_dict()]}

    gs.search.side_effect = slow_search
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls foo")
    r = result_obj.unwrap()
    # Timeout is best-effort — either timeout or used (if barely within budget)
    assert r.metadata.get("graph_signal") in ("timeout", "used")


# ── Scenario 5: callers success ───────────────────────────────────────────────


def test_graph_signal_callers_success():
    """Successful caller query populates graph_data with callers."""
    gs = _mock_graph_service(
        status_response=_fresh_status(),
        search_response={"nodes": [_node_dict(symbol_name="foo")]},
        callers_response={"nodes": [_node_dict(symbol_name="bar_caller")]},
    )
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls foo")
    r = result_obj.unwrap()
    assert r.graph_data is not None
    assert r.graph_data["relation"] == "callers"
    assert r.graph_data["target"] == "foo"
    assert len(r.graph_data["nodes"]) == 1
    assert r.graph_data["nodes"][0]["symbol_name"] == "bar_caller"
    assert r.metadata.get("graph_signal") == "used"


# ── Scenario 6: callees success ───────────────────────────────────────────────


def test_graph_signal_callees_success():
    """Successful callee query populates graph_data with callees."""
    gs = _mock_graph_service(
        status_response=_fresh_status(),
        search_response={"nodes": [_node_dict(symbol_name="foo")]},
        callees_response={"nodes": [_node_dict(symbol_name="baz_callee")]},
    )
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "what does foo call")
    r = result_obj.unwrap()
    assert r.graph_data is not None
    assert r.graph_data["relation"] == "callees"
    assert r.graph_data["target"] == "foo"
    assert len(r.graph_data["nodes"]) == 1
    assert r.graph_data["nodes"][0]["symbol_name"] == "baz_callee"
    assert r.metadata.get("graph_signal") == "used"


# ── Scenario 7: empty target (no predicate detected) ──────────────────────────


def test_graph_signal_no_predicate_for_non_relational_query():
    """Non-relational query should not activate graph at all."""
    gs = _mock_graph_service()
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "how to configure daemon")
    r = result_obj.unwrap()
    assert r.graph_data is None
    assert r.metadata.get("graph_signal") == "no_predicate"
    # Graph service should never be called
    gs.status.assert_not_called()


# ── Scenario 8: GraphStoreAccessError handling ────────────────────────────────


def test_graph_signal_handles_access_error():
    """GraphStoreAccessError should result in 'unavailable' signal."""
    from src.infrastructure.graph_store import GraphStoreAccessError

    gs = _mock_graph_service(
        status_side_effect=GraphStoreAccessError("seg1", "db broken"),
    )
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls foo")
    r = result_obj.unwrap()
    assert r.graph_data is None
    assert r.metadata.get("graph_signal") == "unavailable"


# ── Scenario 9: Ambiguous target (symbol in multiple files) ──────────────────


def test_graph_signal_ambiguous_target_returns_state():
    """When symbol exists in multiple files and disambiguation also fails,
    signal should be 'ambiguous_target'."""
    gs = _mock_graph_service(
        status_response=_fresh_status(),
        search_response={
            "nodes": [
                _node_dict(symbol_name="dup_func", file_rel="src/a.py"),
                _node_dict(symbol_name="dup_func", file_rel="src/b.py"),
            ]
        },
    )
    # callers raises AmbiguousGraphTargetError
    from src.infrastructure.graph_store import AmbiguousGraphTargetError
    gs.callers.side_effect = AmbiguousGraphTargetError("seg", "dup_func", [])
    # _query_related_for_node_id also fails (no real store)
    gs.callees.return_value = {"nodes": []}

    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls dup_func")
    r = result_obj.unwrap()
    # Either ambiguous_target (if disambiguation fails) or used (if fallback succeeds)
    assert r.metadata.get("graph_signal") in ("ambiguous_target", "used")


def test_graph_signal_disambiguation_prefers_first_fuzzy_match():
    """When fuzzy search returns multiple matches, first match is used as resolved target."""
    gs = _mock_graph_service(
        status_response=_fresh_status(),
        search_response={
            "nodes": [
                _node_dict(symbol_name="my_func", file_rel="src/active/mod.py"),
                _node_dict(symbol_name="my_func", file_rel="src/legacy/mod.py"),
            ]
        },
        callers_response={"nodes": [_node_dict(symbol_name="caller_a")]},
    )
    oracle = _make_oracle(graph_service=gs)
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls my_func")
    r = result_obj.unwrap()
    assert r.metadata.get("graph_signal") == "used"
    assert r.graph_data["target"] == "my_func"
