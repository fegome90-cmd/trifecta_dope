import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from src.domain.graph_models import GraphEdge, GraphNode
from src.infrastructure.graph_store import (
    GraphStore,
    GraphStoreIncompleteError,
    GraphStoreSchemaMismatchError,
)


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

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT version FROM schema_version").fetchone()

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

    with pytest.raises(
        GraphStoreSchemaMismatchError,
        match="Graph DB schema version mismatch: expected 1, got 2.",
    ):
        GraphStore(db_path)


def test_graph_store_writable_path_repairs_partial_db_with_valid_schema_version(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "graph.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO schema_version VALUES (?)", (GraphStore.SCHEMA_VERSION,))
    conn.commit()
    conn.close()

    GraphStore(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

    assert {"schema_version", "graph_index", "nodes", "edges"}.issubset(tables)


def test_graph_store_writable_path_does_not_repair_existing_db_without_schema_version(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "graph.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    with pytest.raises(
        GraphStoreIncompleteError,
        match="Graph DB is missing required tables: schema_version.",
    ):
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


def test_graph_store_relations_only_follow_calls_edges(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.db")
    segment_id = "seg_calls_only"
    root = GraphNode(
        id=f"{segment_id}:src/pkg/sample.py:root",
        segment_id=segment_id,
        file_rel="src/pkg/sample.py",
        symbol_name="root",
        qualified_name="root",
        kind="function",
        line=4,
        metadata_json=None,
    )
    leaf = GraphNode(
        id=f"{segment_id}:src/pkg/sample.py:leaf",
        segment_id=segment_id,
        file_rel="src/pkg/sample.py",
        symbol_name="leaf",
        qualified_name="leaf",
        kind="function",
        line=1,
        metadata_json=None,
    )
    reference_edge = GraphEdge(
        id=f"{segment_id}:{root.id}->{leaf.id}:references",
        segment_id=segment_id,
        from_node_id=root.id,
        to_node_id=leaf.id,
        edge_kind="references",
        source="ast",
        confidence=1.0,
    )

    store.replace_segment(segment_id, [root, leaf], [reference_edge])

    assert store.get_callees(segment_id, "root") == []
    assert store.get_callers(segment_id, "leaf") == []


def test_graph_store_relations_are_scoped_to_segment_id(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.db")
    primary_segment = "seg_primary"
    foreign_segment = "seg_foreign"
    target = GraphNode(
        id=f"{primary_segment}:src/pkg/sample.py:leaf",
        segment_id=primary_segment,
        file_rel="src/pkg/sample.py",
        symbol_name="leaf",
        qualified_name="leaf",
        kind="function",
        line=1,
        metadata_json=None,
    )
    foreign_root = GraphNode(
        id=f"{foreign_segment}:src/pkg/other.py:root",
        segment_id=foreign_segment,
        file_rel="src/pkg/other.py",
        symbol_name="root",
        qualified_name="root",
        kind="function",
        line=4,
        metadata_json=None,
    )
    leaking_edge = GraphEdge(
        id=f"{foreign_segment}:{foreign_root.id}->{target.id}:calls",
        segment_id=foreign_segment,
        from_node_id=foreign_root.id,
        to_node_id=target.id,
        edge_kind="calls",
        source="ast",
        confidence=1.0,
    )

    store.replace_segment(primary_segment, [target], [])
    store.replace_segment(foreign_segment, [foreign_root], [leaking_edge])

    assert store.get_callers(primary_segment, "leaf") == []
