from pathlib import Path

import pytest

import src.application.graph_indexer as graph_indexer_module
from src.application.graph_indexer import GraphIndexer
from src.domain.segment_resolver import SegmentRef
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


def test_graph_indexer_does_not_attribute_nested_calls_to_top_level_symbol(
    tmp_path: Path,
) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    def inner():\n"
        "        return leaf()\n"
        "    return inner\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    indexer = GraphIndexer(store=store)

    summary = indexer.index_segment(segment)
    callees = store.get_callees(summary.segment_id, "root")
    callers = store.get_callers(summary.segment_id, "leaf")

    assert summary.edge_count == 0
    assert callees == []
    assert callers == []


def test_graph_indexer_preserves_top_level_edges_when_nested_calls_exist(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    leaf()\n"
        "    def inner():\n"
        "        return leaf()\n"
        "    return inner\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    indexer = GraphIndexer(store=store)

    summary = indexer.index_segment(segment)
    callees = store.get_callees(summary.segment_id, "root")
    callers = store.get_callers(summary.segment_id, "leaf")

    assert summary.edge_count == 1
    assert [node.symbol_name for node in callees] == ["leaf"]
    assert [node.symbol_name for node in callers] == ["root"]


def test_graph_indexer_tracks_direct_constructor_calls_to_top_level_classes(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "class Helper:\n"
        "    pass\n\n"
        "def root():\n"
        "    return Helper()\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    indexer = GraphIndexer(store=store)

    summary = indexer.index_segment(segment)
    callees = store.get_callees(summary.segment_id, "root")
    callers = store.get_callers(summary.segment_id, "Helper")

    assert summary.edge_count == 1
    assert [(node.symbol_name, node.kind) for node in callees] == [("Helper", "class")]
    assert [node.symbol_name for node in callers] == ["root"]


def test_graph_indexer_does_not_treat_nested_call_arguments_as_direct_edges(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def wrapper(value):\n"
        "    return value\n\n"
        "def root():\n"
        "    return wrapper(leaf())\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    indexer = GraphIndexer(store=store)

    summary = indexer.index_segment(segment)
    callees = store.get_callees(summary.segment_id, "root")
    leaf_callers = store.get_callers(summary.segment_id, "leaf")
    wrapper_callers = store.get_callers(summary.segment_id, "wrapper")

    assert summary.edge_count == 1
    assert [node.symbol_name for node in callees] == ["wrapper"]
    assert leaf_callers == []
    assert [node.symbol_name for node in wrapper_callers] == ["root"]


def test_graph_indexer_uses_segment_ref_v1_as_ssot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text("def root():\n    return 1\n")
    fake_ref = SegmentRef(
        root_abs=segment.resolve(),
        slug="segment",
        fingerprint="cafebabe",
        id="segment_cafebabe",
    )

    def fake_resolve(segment_input: Path | str, hash_length: int | None = None) -> SegmentRef:
        assert segment_input == segment
        return fake_ref

    monkeypatch.setattr(graph_indexer_module, "resolve_segment_ref", fake_resolve)

    summary = GraphIndexer().index_segment(segment)

    assert summary.segment_id == fake_ref.id
    assert Path(summary.db_path) == GraphStore.db_path_for_segment(fake_ref.root_abs, fake_ref.id)
