import hashlib
import sqlite3
from pathlib import Path

import pytest

import src.application.graph_service as graph_service_module
from src.application.graph_indexer import GraphIndexer
from src.application.graph_service import GraphService
from src.domain.graph_models import GraphStatus
from src.domain.segment_resolver import SegmentRef, resolve_segment_ref
from src.infrastructure.graph_store import (
    AmbiguousGraphTargetError,
    GraphStore,
    GraphStoreIncompleteError,
)


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


@pytest.mark.parametrize(
    ("method_name", "args", "expected_key", "expected_value"),
    [
        ("status", tuple(), "exists", False),
        ("search", ("root",), "nodes", []),
        ("callers", ("root",), "nodes", []),
        ("callees", ("root",), "nodes", []),
    ],
)
def test_graph_service_injected_store_preserves_pristine_read_semantics(
    tmp_path: Path,
    method_name: str,
    args: tuple[object, ...],
    expected_key: str,
    expected_value: object,
) -> None:
    indexed_segment = tmp_path / "indexed"
    indexed_source_dir = indexed_segment / "src" / "pkg"
    indexed_source_dir.mkdir(parents=True)
    (indexed_source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )
    store = GraphStore(indexed_segment / ".trifecta" / "cache" / "graph_test.db")
    GraphIndexer(store=store).index_segment(indexed_segment)

    pristine_segment = tmp_path / "pristine"
    (pristine_segment / "src").mkdir(parents=True)
    pristine_ref = resolve_segment_ref(pristine_segment)
    pristine_db_path = GraphStore.db_path_for_segment(pristine_ref.root_abs, pristine_ref.id)

    service = GraphService(store=store)
    payload = getattr(service, method_name)(pristine_segment, *args)

    assert payload["status"] == "ok"
    assert payload["segment_id"] == pristine_ref.id
    assert payload[expected_key] == expected_value
    assert not pristine_db_path.exists()


def test_graph_service_ignores_neighbor_injected_store_when_segment_db_exists(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )

    GraphIndexer().index_segment(segment)
    neighbor_store = GraphStore(segment / ".trifecta" / "cache" / "graph_test.db")
    service = GraphService(store=neighbor_store)

    payload = service.status(segment)

    assert payload["status"] == "ok"
    assert payload["node_count"] == 2
    assert payload["edge_count"] == 1


def test_graph_service_accepts_alias_path_for_injected_store(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )
    alias_segment = tmp_path / "segment_alias"
    alias_segment.symlink_to(segment, target_is_directory=True)

    alias_store = GraphStore(alias_segment / ".trifecta" / "cache" / "graph_test.db")
    GraphIndexer(store=alias_store).index_segment(alias_segment)
    service = GraphService(store=alias_store)

    status = service.status(segment)
    search = service.search(segment, "roo")
    callers = service.callers(segment, "leaf")
    callees = service.callees(segment, "root")

    assert status["status"] == "ok"
    assert status["node_count"] == 2
    assert status["edge_count"] == 1
    assert [node["symbol_name"] for node in search["nodes"]] == ["root"]
    assert [node["symbol_name"] for node in callers["nodes"]] == ["root"]
    assert [node["symbol_name"] for node in callees["nodes"]] == ["leaf"]


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


@pytest.mark.parametrize(
    "method_name,args",
    [("status", tuple()), ("search", ("root",)), ("callers", ("root",)), ("callees", ("root",))],
)
def test_graph_service_read_paths_do_not_mutate_partial_db(
    tmp_path: Path, method_name: str, args: tuple[object, ...]
) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)
    segment_ref = resolve_segment_ref(segment)
    db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO schema_version VALUES (?)", (GraphStore.SCHEMA_VERSION,))
    conn.commit()
    conn.close()

    before_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
    service = GraphService()
    method = getattr(service, method_name)

    with pytest.raises(GraphStoreIncompleteError, match="missing required tables"):
        method(segment, *args)

    after_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert after_hash == before_hash


def test_graph_service_status_uses_segment_ref_v1_as_ssot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    segment = tmp_path / "segment"
    segment.mkdir()
    fake_ref = SegmentRef(
        root_abs=segment.resolve(),
        slug="segment",
        fingerprint="deadbeef",
        id="segment_deadbeef",
    )
    seen: dict[str, object] = {}

    def fake_resolve(segment_input: Path | str) -> SegmentRef:
        seen["segment_input"] = segment_input
        return fake_ref

    def fake_probe_status(db_path: Path, segment_id: str) -> GraphStatus:
        seen["db_path"] = db_path
        seen["segment_id"] = segment_id
        return GraphStatus(
            exists=False,
            segment_id=segment_id,
            db_path=str(db_path),
            node_count=0,
            edge_count=0,
            last_indexed_at=None,
        )

    monkeypatch.setattr(graph_service_module, "resolve_segment_ref", fake_resolve)
    monkeypatch.setattr(graph_service_module.GraphStore, "probe_status", fake_probe_status)

    payload = GraphService().status(segment)

    assert seen["segment_input"] == segment
    assert seen["segment_id"] == fake_ref.id
    assert seen["db_path"] == GraphStore.db_path_for_segment(fake_ref.root_abs, fake_ref.id)
    assert payload["segment_id"] == fake_ref.id
