from pathlib import Path

from src.application.graph_indexer import GraphIndexer
from src.application.graph_service import GraphService
from src.domain.segment_resolver import resolve_segment_ref
from src.infrastructure.graph_store import AmbiguousGraphTargetError, GraphStore


def test_graph_service_search_and_status_are_machine_readable(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    GraphIndexer(store=store).index_segment(segment)
    service = GraphService(store=store)

    status = service.status(segment)
    search = service.search(segment, "roo")
    callers = service.callers(segment, "leaf")
    callees = service.callees(segment, "root")

    assert status["status"] == "ok"
    assert status["node_count"] == 2
    assert status["edge_count"] == 1
    assert search["status"] == "ok"
    assert [node["symbol_name"] for node in search["nodes"]] == ["root"]
    assert [node["symbol_name"] for node in callers["nodes"]] == ["root"]
    assert [node["symbol_name"] for node in callees["nodes"]] == ["leaf"]


def test_graph_service_returns_related_terms_without_textual_context(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text("def alpha():\n    return 1\n")

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    GraphIndexer(store=store).index_segment(segment)
    service = GraphService(store=store)

    hints = service.related_terms(segment, "alp")

    assert hints["status"] == "ok"
    assert hints["terms"] == ["alpha", "src/pkg/sample.py"]
    assert "chunks" not in hints
    assert "prompt" not in hints


def test_graph_service_status_does_not_create_db_for_pristine_segment(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)
    service = GraphService()

    status = service.status(segment)
    segment_ref = resolve_segment_ref(segment)
    db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)

    assert status["status"] == "ok"
    assert status["exists"] is False
    assert status["last_indexed_at"] is None
    assert not db_path.exists()


def test_graph_service_callers_fail_closed_on_ambiguous_symbol(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "first.py").write_text(
        "def helper():\n"
        "    return 1\n\n"
        "def root_one():\n"
        "    return helper()\n"
    )
    (source_dir / "second.py").write_text(
        "def helper():\n"
        "    return 2\n\n"
        "def root_two():\n"
        "    return helper()\n"
    )

    store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    GraphIndexer(store=store).index_segment(segment)
    service = GraphService(store=store)

    try:
        service.callers(segment, "helper")
    except AmbiguousGraphTargetError as exc:
        assert exc.symbol == "helper"
        assert [candidate["file_rel"] for candidate in exc.candidates] == [
            "src/pkg/first.py",
            "src/pkg/second.py",
        ]
    else:
        raise AssertionError("Expected AmbiguousGraphTargetError for duplicate symbol")
