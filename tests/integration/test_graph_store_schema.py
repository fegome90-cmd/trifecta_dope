import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from src.domain.graph_models import GraphEdge, GraphNode
from src.infrastructure.graph_store import GraphStore


def _sample_node(segment_id: str = "seg_1234") -> GraphNode:
    return GraphNode(
        id="seg_1234:src/pkg/sample.py:root",
        segment_id=segment_id,
        file_rel="src/pkg/sample.py",
        symbol_name="root",
        qualified_name="root",
        kind="function",
        line=4,
        metadata_json=None,
    )


def _sample_edge(segment_id: str = "seg_1234") -> GraphEdge:
    return GraphEdge(
        id="seg_1234:root->leaf:calls",
        segment_id=segment_id,
        from_node_id="seg_1234:src/pkg/sample.py:root",
        to_node_id="seg_1234:src/pkg/sample.py:leaf",
        edge_kind="calls",
        source="ast",
        confidence=None,
    )


def test_graph_store_initializes_schema_and_reports_empty_status(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"

    store = GraphStore(db_path)
    status = store.get_status("seg_1234")

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    conn.close()

    assert row == (1,)
    assert status.exists is True
    assert status.segment_id == "seg_1234"
    assert status.node_count == 0
    assert status.edge_count == 0
    assert status.last_indexed_at is None


def test_graph_store_fails_closed_on_wrong_schema_version(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO schema_version VALUES (2)")
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="schema version mismatch: expected 1, got 2"):
        GraphStore(db_path)


def test_graph_store_roundtrips_nodes_and_edges(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.db")

    leaf_node = replace(
        _sample_node(),
        id="seg_1234:src/pkg/sample.py:leaf",
        symbol_name="leaf",
        qualified_name="leaf",
        line=1,
    )

    store.replace_segment("seg_1234", [_sample_node(), leaf_node], [_sample_edge()])

    status = store.get_status("seg_1234")
    results = store.search_nodes("seg_1234", "root")
    callees = store.get_callees("seg_1234", "root")
    callers = store.get_callers("seg_1234", "leaf")

    assert status.node_count == 2
    assert status.edge_count == 1
    assert len(results) == 1
    assert results[0].symbol_name == "root"
    assert [node.symbol_name for node in callees] == ["leaf"]
    assert [node.symbol_name for node in callers] == ["root"]
