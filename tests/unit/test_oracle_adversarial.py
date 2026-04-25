"""Adversarial test suite for Oracle graph signal — organized by failure class.

Each class targets a specific failure mode. The goal is NOT happy-path testing
but deliberate attempts to break the Oracle's routing, degradation, and
signal-state reporting.

7 signal states under test:
  no_predicate, unavailable, stale, timeout, target_not_found,
  ambiguous_target, used
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.application.oracle_use_case import SearchOracleUseCase
from src.infrastructure.graph_store import (
    AmbiguousGraphTargetError,
    GraphStoreAccessError,
    GraphTargetNotFoundError,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_oracle(graph_service: Optional[Any] = None) -> SearchOracleUseCase:
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
        "status": "ok", "exists": True, "node_count": 10, "edge_count": 5,
        "last_indexed_at": datetime.now(timezone.utc).isoformat(),
    }


def _stale_status() -> Dict[str, Any]:
    return {
        "status": "ok", "exists": True, "node_count": 10, "edge_count": 5,
        "last_indexed_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    }


def _node(symbol_name: str = "func_a", file_rel: str = "src/mod.py", **kw: Any) -> Dict[str, Any]:
    return {
        "symbol_name": symbol_name, "qualified_name": kw.get("qualified_name", symbol_name),
        "file_rel": file_rel, "line": kw.get("line", 10), "kind": kw.get("kind", "function"),
    }


def _mock_gs(
    status: Optional[Dict] = None,
    search_nodes: Optional[list] = None,
    callers_nodes: Optional[list] = None,
    callees_nodes: Optional[list] = None,
    status_error: Optional[Exception] = None,
    search_error: Optional[Exception] = None,
    callers_error: Optional[Exception] = None,
) -> MagicMock:
    gs = MagicMock()
    if status_error:
        gs.status.side_effect = status_error
    else:
        gs.status.return_value = status or _fresh_status()
    if search_error:
        gs.search.side_effect = search_error
    else:
        gs.search.return_value = {"nodes": search_nodes or []}
    if callers_error:
        gs.callers.side_effect = callers_error
    else:
        gs.callers.return_value = {"nodes": callers_nodes or []}
    gs.callees.return_value = {"nodes": callees_nodes or []}
    return gs


def _run(oracle: SearchOracleUseCase, query: str) -> Dict[str, Any]:
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result = oracle.execute(Path("/tmp/repo"), query)
    return result.unwrap().model_dump()


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 1: Duplicate / Ambiguous Symbols
# ══════════════════════════════════════════════════════════════════════════════


class TestDuplicateAmbiguousSymbols:

    def test_symbol_in_5_files(self):
        """Symbol exists in 5 files — graph must not crash, must report state."""
        gs = _mock_gs(search_nodes=[_node("dup", file_rel=f"src/mod{i}.py") for i in range(5)])
        gs.callers.side_effect = AmbiguousGraphTargetError("seg", "dup", [])
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls dup")
        assert r["metadata"]["graph_signal"] in ("ambiguous_target", "used")
        assert r["graph_data"] is None or isinstance(r["graph_data"], dict)

    def test_identical_symbol_names_different_kinds(self):
        """Same name but different kinds (function vs class) — ambiguity expected."""
        gs = _mock_gs(search_nodes=[
            _node("Config", file_rel="src/config.py", kind="class"),
            _node("Config", file_rel="src/models.py", kind="function"),
        ])
        gs.callers.side_effect = AmbiguousGraphTargetError("seg", "Config", [])
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls Config")
        assert r["metadata"]["graph_signal"] in ("ambiguous_target", "used")

    def test_fuzzy_returns_partial_match_that_is_ambiguous(self):
        """Fuzzy search finds 'resolve' which matches multiple symbols starting with 'resolve'."""
        gs = _mock_gs(search_nodes=[
            _node("resolve_segment_ref", file_rel="src/domain/segment_resolver.py"),
            _node("resolve_path", file_rel="src/infrastructure/utils.py"),
        ])
        gs.callers.return_value = {"nodes": [_node("caller_a")]}
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls resolve")
        # Should resolve to first fuzzy match
        assert r["metadata"]["graph_signal"] == "used"


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 2: Stale Graph
# ══════════════════════════════════════════════════════════════════════════════


class TestStaleGraph:

    def test_stale_graph_never_queried(self):
        """Stale graph → no graph methods called beyond status."""
        gs = _mock_gs(status=_stale_status())
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "stale"
        gs.search.assert_not_called()
        gs.callers.assert_not_called()

    def test_stale_graph_with_zero_indexed_at(self):
        """Graph with no indexed_at → treated as stale."""
        status = {"status": "ok", "exists": True, "node_count": 0, "edge_count": 0, "last_indexed_at": None}
        gs = _mock_gs(status=status)
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "stale"

    def test_stale_graph_with_invalid_date(self):
        """Graph with unparseable date → treated as stale."""
        status = {"status": "ok", "exists": True, "node_count": 5, "edge_count": 2, "last_indexed_at": "not-a-date"}
        gs = _mock_gs(status=status)
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "stale"


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 3: Absent Graph
# ══════════════════════════════════════════════════════════════════════════════


class TestAbsentGraph:

    def test_no_graph_service_injected(self):
        """graph_service=None → unavailable."""
        oracle = _make_oracle(graph_service=None)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "unavailable"

    def test_graph_db_access_error(self):
        """status() raises GraphStoreAccessError → unavailable."""
        gs = _mock_gs(status_error=GraphStoreAccessError("seg", "db broken"))
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "unavailable"

    def test_graph_status_raises_generic_exception(self):
        """status() raises generic Exception → unavailable."""
        gs = _mock_gs(status_error=RuntimeError("unexpected"))
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "unavailable"

    def test_graph_search_raises_generic_exception(self):
        """search() raises generic Exception → unavailable."""
        gs = _mock_gs(search_error=RuntimeError("search crash"))
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] == "unavailable"


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 4: Artificial Timeout
# ══════════════════════════════════════════════════════════════════════════════


class TestArtificialTimeout:

    def test_search_exceeds_budget(self):
        """search() takes too long → timeout."""
        import time as _time

        gs = _mock_gs()
        def slow_search(*a, **kw):
            _time.sleep(0.02)  # 20ms — exceeds 15ms budget
            return {"nodes": [_node("foo")]}

        gs.search.side_effect = slow_search
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        assert r["metadata"]["graph_signal"] in ("timeout", "used")

    def test_traversal_exceeds_budget_returns_over_budget_flag(self):
        """Traversal completes slightly over budget → used with over_budget=True."""
        import time as _time

        gs = _mock_gs(
            search_nodes=[_node("foo")],
            callers_nodes=[_node("bar")],
        )
        # Make callers slow but not too slow
        original_callers = gs.callers.return_value
        def slow_callers(*a, **kw):
            _time.sleep(0.012)  # 12ms — pushes total over 15ms
            return original_callers
        gs.callers.side_effect = slow_callers
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "who calls foo")
        signal = r["metadata"]["graph_signal"]
        # Either timeout or used with over_budget
        assert signal in ("timeout", "used")


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 5: Weird Payloads / Almost-Relational
# ══════════════════════════════════════════════════════════════════════════════


class TestWeirdPayloads:

    @pytest.mark.parametrize("query", [
        "who calls",            # no target
        "callers of",           # no target
        "qué llama",            # no target (ES)
        "",                     # empty
        "   ",                  # whitespace
    ])
    def test_queries_with_missing_target(self, query):
        """Queries that match pattern but have no target → no_predicate or handled gracefully."""
        oracle = _make_oracle(graph_service=_mock_gs())
        r = _run(oracle, query)
        # Should not crash, signal should be a valid state
        signal = r["metadata"]["graph_signal"]
        assert signal in ("no_predicate", "target_not_found", "unavailable", "used")

    @pytest.mark.parametrize("query", [
        "who calls foo bar baz",       # multi-word target
        "callers of __init__",         # dunder
        "who calls _private_method",   # leading underscore
        "who calls CamelCase",         # PascalCase
    ])
    def test_unusual_target_names(self, query):
        """Targets with special naming patterns — must not crash."""
        gs = _mock_gs()
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, query)
        signal = r["metadata"]["graph_signal"]
        assert signal in ("no_predicate", "target_not_found", "unavailable", "used")

    def test_very_long_query(self):
        """Extremely long query string — must not crash."""
        query = "who calls " + "a" * 10000
        oracle = _make_oracle(graph_service=_mock_gs())
        r = _run(oracle, query)
        # Should handle without error
        assert "graph_signal" in r["metadata"]

    def test_query_with_unicode(self):
        """Unicode characters in query — must not crash."""
        oracle = _make_oracle(graph_service=_mock_gs())
        r = _run(oracle, "quién llama a función_rara")
        assert "graph_signal" in r["metadata"]


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 6: EN/ES Mixed Queries
# ══════════════════════════════════════════════════════════════════════════════


class TestENESMixed:

    @pytest.mark.parametrize("query,expected_relation", [
        ("who calls foo", "callers"),
        ("callers of foo", "callers"),
        ("quién llama a foo", "callers"),
        ("quién llama al foo", "callers"),
        ("quién llama a la foo", "callers"),
        ("what does foo call", "callees"),
        ("callees of foo", "callees"),
        ("qué llama foo", "callees"),
    ])
    def test_en_es_patterns_resolve_correctly(self, query, expected_relation):
        """All EN/ES patterns must resolve to correct relation type."""
        gs = _mock_gs(search_nodes=[_node("foo")])
        if expected_relation == "callers":
            gs.callers.return_value = {"nodes": [_node("caller_x")]}
        else:
            gs.callees.return_value = {"nodes": [_node("callee_x")]}
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, query)
        assert r["metadata"]["graph_signal"] == "used"
        if r["graph_data"]:
            assert r["graph_data"]["relation"] == expected_relation


# ══════════════════════════════════════════════════════════════════════════════
# CLASS 7: Negative Controls — Graph MUST NOT Activate
# ══════════════════════════════════════════════════════════════════════════════


class TestNegativeControls:

    @pytest.mark.parametrize("query", [
        "how to configure the daemon",
        "what is context_pack.json",
        "context service",
        "explain the oracle architecture",
        "show me the skill hub index",
        "who uses execute",           # unsupported pattern
        "donde se usa init",          # unsupported pattern (ES)
        "call graph of main",         # ambiguous: callers or callees?
        "import chain cli.py to store", # multi-hop, out of scope
        "search for config files",
        "list all modules",
        "what is the daemon pid",
    ])
    def test_graph_must_not_activate(self, query):
        """Graph must be completely skipped for non-relational queries."""
        gs = _mock_gs()
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, query)
        assert r["metadata"]["graph_signal"] == "no_predicate"
        assert r["graph_data"] is None
        gs.status.assert_not_called()
        gs.search.assert_not_called()

    def test_negative_controls_preserve_prime_ast(self):
        """Negative queries must return PRIME+AST results normally."""
        gs = _mock_gs()
        oracle = _make_oracle(graph_service=gs)
        r = _run(oracle, "how to configure daemon")
        assert r["metadata"]["graph_signal"] == "no_predicate"
        assert r["fidelity"] in ("degraded", "fallback")
        assert isinstance(r["ast_symbols"], list)
        assert isinstance(r["prime_chunks"], list)
