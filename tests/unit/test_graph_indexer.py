from pathlib import Path

from src.application.graph_indexer import GraphIndexer
from src.infrastructure.graph_store import GraphStore


def test_graph_indexer_extracts_top_level_nodes_and_direct_call_edges(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n\n"
        "class Helper:\n"
        "    pass\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    indexer = GraphIndexer(store=store)

    summary = indexer.index_segment(segment)
    status = store.get_status(summary.segment_id)
    callees = store.get_callees(summary.segment_id, "root")
    callers = store.get_callers(summary.segment_id, "leaf")

    assert summary.node_count == 3
    assert summary.edge_count == 1
    assert status.node_count == 3
    assert status.edge_count == 1
    assert [node.symbol_name for node in callees] == ["leaf"]
    assert [node.symbol_name for node in callers] == ["root"]
