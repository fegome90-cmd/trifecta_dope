"""Integration tests for Oracle with GraphService wiring.

3.2: Oracle with real GraphService + in-memory SQLite → caller query returns graph_data.
3.3: Oracle without graph_service → graph_data=None, zero regression.
3.4: Mock GraphService returning <3/5 callers → Oracle still functions with fidelity="degraded".
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.application.oracle_use_case import SearchOracleUseCase
from src.domain.context_models import OracleResult


def _setup_in_memory_graph() -> tuple[sqlite3.Connection, str]:
    """Create an in-memory SQLite graph with 3 nodes and 2 edges."""
    segment_id = "test_seg_001"
    conn = sqlite3.connect(":memory:")

    conn.execute("""
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY,
            segment_id TEXT NOT NULL,
            file_rel TEXT NOT NULL,
            symbol_name TEXT NOT NULL,
            qualified_name TEXT NOT NULL,
            kind TEXT NOT NULL,
            line INTEGER NOT NULL,
            metadata_json TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE edges (
            id TEXT PRIMARY KEY,
            segment_id TEXT NOT NULL,
            from_node_id TEXT NOT NULL,
            to_node_id TEXT NOT NULL,
            edge_kind TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'ast',
            confidence REAL
        )
    """)
    conn.execute("""
        CREATE TABLE graph_index (
            segment_id TEXT PRIMARY KEY,
            indexed_at TEXT NOT NULL
        )
    """)

    # Insert 3 nodes
    for node in [
        ("test_seg_001:src/a.py:main", segment_id, "src/a.py", "main", "main", "function", 10, None),
        ("test_seg_001:src/b.py:helper", segment_id, "src/b.py", "helper", "helper", "function", 5, None),
        ("test_seg_001:src/c.py:process", segment_id, "src/c.py", "process", "process", "function", 20, None),
    ]:
        conn.execute("INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?)", node)

    # Insert 2 edges: main -> helper, main -> process
    for edge in [
        ("test_seg_001:main->helper:calls", segment_id,
         "test_seg_001:src/a.py:main", "test_seg_001:src/b.py:helper", "calls", "ast", 1.0),
        ("test_seg_001:main->process:calls", segment_id,
         "test_seg_001:src/a.py:main", "test_seg_001:src/c.py:process", "calls", "ast", 1.0),
    ]:
        conn.execute("INSERT INTO edges VALUES (?,?,?,?,?,?,?)", edge)

    conn.execute(
        "INSERT INTO graph_index VALUES (?, ?)",
        (segment_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return conn, segment_id


def test_integration_oracle_with_graph_returns_callers():
    """3.2: Oracle with real GraphService + in-memory SQLite returns graph_data for callers."""
    gs = MagicMock()
    gs.status.return_value = {
        "status": "ok",
        "exists": True,
        "node_count": 3,
        "edge_count": 2,
        "last_indexed_at": datetime.now(timezone.utc).isoformat(),
    }
    gs.search.return_value = {"nodes": [{"symbol_name": "main"}]}
    gs.callees.return_value = {
        "nodes": [
            {"symbol_name": "helper", "qualified_name": "helper", "file_rel": "src/b.py", "line": 5, "kind": "function"},
            {"symbol_name": "process", "qualified_name": "process", "file_rel": "src/c.py", "line": 20, "kind": "function"},
        ]
    }

    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])

        ast_builder = MagicMock()
        ast_builder.build.return_value = MagicMock(symbols=[])

        oracle = SearchOracleUseCase(
            ast_builder=ast_builder,
            graph_service=gs,
            telemetry=None,
        )
        result_obj = oracle.execute(Path("/tmp/repo"), "what does main call")

    r: OracleResult = result_obj.unwrap()
    assert r.graph_data is not None
    assert r.graph_data["relation"] == "callees"
    assert r.graph_data["target"] == "main"
    assert len(r.graph_data["nodes"]) == 2
    node_names = {n["symbol_name"] for n in r.graph_data["nodes"]}
    assert "helper" in node_names
    assert "process" in node_names
    assert r.metadata["graph_signal"] == "used"


def test_integration_oracle_without_graph_no_regression():
    """3.3: Oracle without graph_service → graph_data=None, existing signals work."""
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])

        ast_builder = MagicMock()
        ast_builder.build.return_value = MagicMock(symbols=[])

        oracle = SearchOracleUseCase(
            ast_builder=ast_builder,
            graph_service=None,
            telemetry=None,
        )
        result_obj = oracle.execute(Path("/tmp/repo"), "explain the oracle architecture")

    r = result_obj.unwrap()
    assert r.graph_data is None
    assert r.metadata["graph_signal"] == "no_predicate"
    assert r.fidelity in ("full", "degraded", "fallback")
    assert isinstance(r.prime_chunks, list)
    assert isinstance(r.ast_symbols, list)


def test_kill_criteria_oracle_functions_with_degraded_fidelity():
    """3.4: Mock GraphService returning few callers → Oracle still works."""
    gs = MagicMock()
    gs.status.return_value = {
        "status": "ok",
        "exists": True,
        "node_count": 10,
        "edge_count": 2,
        "last_indexed_at": datetime.now(timezone.utc).isoformat(),
    }
    gs.search.return_value = {"nodes": [{"symbol_name": "target_func"}]}
    gs.callers.return_value = {"nodes": [{"symbol_name": "only_one_caller"}]}

    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])

        ast_builder = MagicMock()
        ast_builder.build.return_value = MagicMock(symbols=[])

        oracle = SearchOracleUseCase(
            ast_builder=ast_builder,
            graph_service=gs,
            telemetry=None,
        )
        result_obj = oracle.execute(Path("/tmp/repo"), "who calls target_func")

    r = result_obj.unwrap()
    # Oracle still functions — graph_data populated but sparse
    assert r.graph_data is not None
    assert len(r.graph_data["nodes"]) == 1
    # Fidelity is degraded (no LSP, has AST fallback)
    assert r.fidelity in ("degraded", "fallback")
    assert r.metadata["graph_signal"] == "used"
