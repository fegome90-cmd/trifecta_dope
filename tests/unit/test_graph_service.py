from pathlib import Path

from src.application.graph_indexer import GraphIndexer
from src.application.graph_service import GraphService
from src.infrastructure.graph_store import GraphStore


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
