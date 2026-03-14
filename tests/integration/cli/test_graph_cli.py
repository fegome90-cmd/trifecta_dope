import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.domain.segment_resolver import resolve_segment_ref
from src.infrastructure.graph_store import GraphStore
from src.infrastructure.cli import app


runner = CliRunner()


def _graph_cache_paths(segment: Path) -> tuple[Path, Path]:
    segment_ref = resolve_segment_ref(segment)
    db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)
    return db_path, db_path.parent


def _write_schema_only_db(segment: Path, version: int = GraphStore.SCHEMA_VERSION) -> tuple[str, Path]:
    db_path, cache_dir = _graph_cache_paths(segment)
    cache_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO schema_version VALUES (?)", (version,))
    conn.commit()
    conn.close()
    return hashlib.sha256(db_path.read_bytes()).hexdigest(), db_path


def _write_sqlite_db_without_schema_version(segment: Path) -> Path:
    db_path, cache_dir = _graph_cache_paths(segment)
    cache_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    return db_path


def _make_db_path_unavailable(segment: Path) -> Path:
    db_path, cache_dir = _graph_cache_paths(segment)
    cache_dir.mkdir(parents=True, exist_ok=True)
    db_path.mkdir()
    return db_path


def test_graph_cli_help_and_index_status_search_flow(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )

    help_result = runner.invoke(app, ["graph", "--help"])
    assert help_result.exit_code == 0
    assert "index" in help_result.output
    assert "status" in help_result.output

    index_result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    assert index_result.exit_code == 0, index_result.output
    index_output = json.loads(index_result.output)
    assert index_output["status"] == "ok"
    assert index_output["node_count"] == 2

    status_result = runner.invoke(app, ["graph", "status", "--segment", str(segment), "--json"])
    assert status_result.exit_code == 0, status_result.output
    status_output = json.loads(status_result.output)
    assert status_output["status"] == "ok"
    assert status_output["node_count"] == 2
    assert status_output["edge_count"] == 1

    search_result = runner.invoke(
        app,
        ["graph", "search", "--segment", str(segment), "--query", "root", "--json"],
    )
    assert search_result.exit_code == 0, search_result.output
    search_output = json.loads(search_result.output)
    assert [node["symbol_name"] for node in search_output["nodes"]] == ["root"]


def test_graph_cli_callers_and_callees_are_honest_for_simple_fixture(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )

    runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])

    callers_result = runner.invoke(
        app,
        ["graph", "callers", "--segment", str(segment), "--symbol", "leaf", "--json"],
    )
    callees_result = runner.invoke(
        app,
        ["graph", "callees", "--segment", str(segment), "--symbol", "root", "--json"],
    )

    assert callers_result.exit_code == 0, callers_result.output
    assert callees_result.exit_code == 0, callees_result.output
    assert [node["symbol_name"] for node in json.loads(callers_result.output)["nodes"]] == ["root"]
    assert [node["symbol_name"] for node in json.loads(callees_result.output)["nodes"]] == ["leaf"]


def test_graph_cli_status_does_not_create_db_for_pristine_segment(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)

    status_result = runner.invoke(app, ["graph", "status", "--segment", str(segment), "--json"])
    status_output = json.loads(status_result.output)
    db_path, cache_dir = _graph_cache_paths(segment)

    assert status_result.exit_code == 0, status_result.output
    assert status_output["status"] == "ok"
    assert status_output["exists"] is False
    assert status_output["last_indexed_at"] is None
    assert not db_path.exists()
    assert not cache_dir.exists()


@pytest.mark.parametrize(
    ("command", "args", "expected_key", "expected_value"),
    [
        ("search", ["--query", "root"], "nodes", []),
        ("callers", ["--symbol", "root"], "nodes", []),
        ("callees", ["--symbol", "root"], "nodes", []),
    ],
)
def test_graph_cli_read_paths_do_not_create_db_for_pristine_segment(
    tmp_path: Path,
    command: str,
    args: list[str],
    expected_key: str,
    expected_value: list[object],
) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)

    result = runner.invoke(app, ["graph", command, "--segment", str(segment), *args, "--json"])
    payload = json.loads(result.output)
    db_path, cache_dir = _graph_cache_paths(segment)

    assert result.exit_code == 0, result.output
    assert payload["status"] == "ok"
    assert payload[expected_key] == expected_value
    assert not db_path.exists()
    assert not cache_dir.exists()


def test_graph_cli_callees_ignore_nested_function_calls(tmp_path: Path) -> None:
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

    index_result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    callees_result = runner.invoke(
        app,
        ["graph", "callees", "--segment", str(segment), "--symbol", "root", "--json"],
    )

    assert index_result.exit_code == 0, index_result.output
    assert callees_result.exit_code == 0, callees_result.output
    assert json.loads(index_result.output)["edge_count"] == 0
    assert json.loads(callees_result.output)["nodes"] == []


@pytest.mark.parametrize("command", ["callers", "callees"])
def test_graph_cli_related_commands_return_stable_json_for_ambiguous_symbol(
    tmp_path: Path, command: str
) -> None:
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

    index_result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    result = runner.invoke(
        app,
        ["graph", command, "--segment", str(segment), "--symbol", "helper", "--json"],
    )

    assert index_result.exit_code == 0, index_result.output
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["symbol"] == "helper"
    assert payload["error"] == {
        "code": "GRAPH_TARGET_AMBIGUOUS",
        "kind": "ambiguous_symbol",
        "message": "Symbol 'helper' matched multiple graph nodes.",
        "details": {},
        "candidates": [
            {
                "id": payload["error"]["candidates"][0]["id"],
                "segment_id": payload["error"]["candidates"][0]["segment_id"],
                "file_rel": "src/pkg/first.py",
                "symbol_name": "helper",
                "qualified_name": "helper",
                "kind": "function",
                "line": 1,
                "metadata_json": None,
            },
            {
                "id": payload["error"]["candidates"][1]["id"],
                "segment_id": payload["error"]["candidates"][1]["segment_id"],
                "file_rel": "src/pkg/second.py",
                "symbol_name": "helper",
                "qualified_name": "helper",
                "kind": "function",
                "line": 1,
                "metadata_json": None,
            },
        ],
    }


@pytest.mark.parametrize("command", ["callers", "callees"])
def test_graph_cli_related_commands_return_distinct_json_for_missing_symbol(
    tmp_path: Path, command: str
) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def helper():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return helper()\n"
    )

    index_result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    result = runner.invoke(
        app,
        ["graph", command, "--segment", str(segment), "--symbol", "missing", "--json"],
    )

    assert index_result.exit_code == 0, index_result.output
    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["symbol"] == "missing"
    assert payload["error"] == {
        "code": "GRAPH_TARGET_NOT_FOUND",
        "kind": "symbol_not_found",
        "message": "Symbol 'missing' was not found in the graph index.",
        "details": {},
        "candidates": [],
    }


@pytest.mark.parametrize(
    ("command", "args", "expected_code"),
    [
        ("status", [], "GRAPH_DB_INCOMPLETE"),
        ("search", ["--query", "root"], "GRAPH_DB_INCOMPLETE"),
        ("callers", ["--symbol", "root"], "GRAPH_DB_INCOMPLETE"),
        ("callees", ["--symbol", "root"], "GRAPH_DB_INCOMPLETE"),
    ],
)
def test_graph_cli_read_paths_do_not_mutate_partial_db(
    tmp_path: Path, command: str, args: list[str], expected_code: str
) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)
    before_hash, db_path = _write_schema_only_db(segment)

    result = runner.invoke(app, ["graph", command, "--segment", str(segment), *args, "--json"])
    payload = json.loads(result.output)
    after_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()

    assert result.exit_code == 1, result.output
    assert after_hash == before_hash
    expected_payload: dict[str, object] = {
        "status": "error",
        "segment_id": resolve_segment_ref(segment).id,
        "error": {
            "code": expected_code,
            "kind": "graph_db_incomplete",
            "message": "Graph DB is missing required tables: edges, graph_index, nodes.",
            "details": {"missing_tables": ["edges", "graph_index", "nodes"]},
        },
    }
    if command in {"callers", "callees"}:
        expected_payload["symbol"] = "root"
    assert payload == expected_payload


@pytest.mark.parametrize(
    ("command", "args", "expected_symbol"),
    [
        ("status", [], None),
        ("search", ["--query", "root"], None),
        ("callers", ["--symbol", "root"], "root"),
        ("callees", ["--symbol", "root"], "root"),
        ("index", [], None),
    ],
)
def test_graph_cli_returns_stable_json_for_schema_mismatch(
    tmp_path: Path, command: str, args: list[str], expected_symbol: str | None
) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)
    _write_schema_only_db(segment, version=999)

    result = runner.invoke(app, ["graph", command, "--segment", str(segment), *args, "--json"])
    payload = json.loads(result.output)

    assert result.exit_code == 1, result.output
    assert payload["status"] == "error"
    assert payload["segment_id"] == resolve_segment_ref(segment).id
    if expected_symbol is None:
        assert "symbol" not in payload
    else:
        assert payload["symbol"] == expected_symbol
    assert payload["error"] == {
        "code": "GRAPH_DB_SCHEMA_MISMATCH",
        "kind": "graph_db_schema_mismatch",
        "message": "Graph DB schema version mismatch: expected 1, got 999.",
        "details": {"expected_version": 1, "actual_version": 999},
    }


@pytest.mark.parametrize(
    ("command", "args", "expected_symbol"),
    [
        ("status", [], None),
        ("search", ["--query", "root"], None),
        ("callers", ["--symbol", "root"], "root"),
        ("callees", ["--symbol", "root"], "root"),
        ("index", [], None),
    ],
)
def test_graph_cli_returns_stable_json_for_unavailable_db(
    tmp_path: Path, command: str, args: list[str], expected_symbol: str | None
) -> None:
    segment = tmp_path / "segment"
    (segment / "src").mkdir(parents=True)
    _make_db_path_unavailable(segment)

    result = runner.invoke(app, ["graph", command, "--segment", str(segment), *args, "--json"])
    payload = json.loads(result.output)

    assert result.exit_code == 1, result.output
    assert payload["status"] == "error"
    assert payload["segment_id"] == resolve_segment_ref(segment).id
    if expected_symbol is None:
        assert "symbol" not in payload
    else:
        assert payload["symbol"] == expected_symbol
    assert payload["error"]["code"] == "GRAPH_DB_UNAVAILABLE"
    assert payload["error"]["kind"] == "graph_db_unavailable"
    assert payload["error"]["details"] == {}


def test_graph_cli_index_fails_closed_for_existing_db_without_schema_version(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text("def root():\n    return 1\n")
    _write_sqlite_db_without_schema_version(segment)

    result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    payload = json.loads(result.output)

    assert result.exit_code == 1, result.output
    assert payload == {
        "status": "error",
        "segment_id": resolve_segment_ref(segment).id,
        "error": {
            "code": "GRAPH_DB_INCOMPLETE",
            "kind": "graph_db_incomplete",
            "message": "Graph DB is missing required tables: schema_version.",
            "details": {"missing_tables": ["schema_version"]},
        },
    }


@pytest.mark.parametrize(
    ("command", "args", "expected_exit"),
    [
        ("index", [], 0),
        ("status", [], 0),
        ("search", ["--query", "root"], 0),
        ("callers", ["--symbol", "leaf"], 0),
        ("callees", ["--symbol", "root"], 0),
    ],
)
def test_graph_cli_success_exit_code_matrix(
    tmp_path: Path, command: str, args: list[str], expected_exit: int
) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )

    if command != "index":
        runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])

    result = runner.invoke(app, ["graph", command, "--segment", str(segment), *args, "--json"])

    assert result.exit_code == expected_exit, result.output


@pytest.mark.parametrize(
    ("command", "args", "setup_kind", "expected_code"),
    [
        ("callers", ["--symbol", "missing"], "missing", "GRAPH_TARGET_NOT_FOUND"),
        ("callees", ["--symbol", "missing"], "missing", "GRAPH_TARGET_NOT_FOUND"),
        ("callers", ["--symbol", "helper"], "ambiguous", "GRAPH_TARGET_AMBIGUOUS"),
        ("callees", ["--symbol", "helper"], "ambiguous", "GRAPH_TARGET_AMBIGUOUS"),
        ("status", [], "unavailable", "GRAPH_DB_UNAVAILABLE"),
        ("search", ["--query", "root"], "unavailable", "GRAPH_DB_UNAVAILABLE"),
        ("callers", ["--symbol", "root"], "unavailable", "GRAPH_DB_UNAVAILABLE"),
        ("callees", ["--symbol", "root"], "unavailable", "GRAPH_DB_UNAVAILABLE"),
        ("index", [], "unavailable", "GRAPH_DB_UNAVAILABLE"),
        ("status", [], "incomplete", "GRAPH_DB_INCOMPLETE"),
        ("search", ["--query", "root"], "incomplete", "GRAPH_DB_INCOMPLETE"),
        ("callers", ["--symbol", "root"], "incomplete", "GRAPH_DB_INCOMPLETE"),
        ("callees", ["--symbol", "root"], "incomplete", "GRAPH_DB_INCOMPLETE"),
        ("index", [], "invalid_missing_schema", "GRAPH_DB_INCOMPLETE"),
        ("status", [], "schema_mismatch", "GRAPH_DB_SCHEMA_MISMATCH"),
        ("search", ["--query", "root"], "schema_mismatch", "GRAPH_DB_SCHEMA_MISMATCH"),
        ("callers", ["--symbol", "root"], "schema_mismatch", "GRAPH_DB_SCHEMA_MISMATCH"),
        ("callees", ["--symbol", "root"], "schema_mismatch", "GRAPH_DB_SCHEMA_MISMATCH"),
        ("index", [], "schema_mismatch", "GRAPH_DB_SCHEMA_MISMATCH"),
    ],
)
def test_graph_cli_failure_exit_code_matrix(
    tmp_path: Path, command: str, args: list[str], setup_kind: str, expected_code: str
) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def helper():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return helper()\n"
    )

    if setup_kind == "missing":
        runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    elif setup_kind == "ambiguous":
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
        runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    elif setup_kind == "unavailable":
        _make_db_path_unavailable(segment)
    elif setup_kind == "incomplete":
        _write_schema_only_db(segment)
    elif setup_kind == "invalid_missing_schema":
        _write_sqlite_db_without_schema_version(segment)
    elif setup_kind == "schema_mismatch":
        _write_schema_only_db(segment, version=999)
    else:
        raise AssertionError(f"Unknown setup_kind: {setup_kind}")

    result = runner.invoke(app, ["graph", command, "--segment", str(segment), *args, "--json"])
    payload = json.loads(result.output)

    assert result.exit_code == 1, result.output
    assert payload["error"]["code"] == expected_code


def test_graph_cli_index_repairs_partial_db_with_valid_schema_version(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    source_dir = segment / "src" / "pkg"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.py").write_text(
        "def leaf():\n"
        "    return 1\n\n"
        "def root():\n"
        "    return leaf()\n"
    )
    _, db_path = _write_schema_only_db(segment)

    result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    payload = json.loads(result.output)

    assert result.exit_code == 0, result.output
    assert payload["status"] == "ok"
    assert payload["node_count"] == 2
    assert payload["edge_count"] == 1

    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    conn.close()
    assert {"schema_version", "graph_index", "nodes", "edges"}.issubset(tables)


def test_graph_cli_keeps_top_level_edge_while_ignoring_nested_calls(tmp_path: Path) -> None:
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

    index_result = runner.invoke(app, ["graph", "index", "--segment", str(segment), "--json"])
    callers_result = runner.invoke(
        app,
        ["graph", "callers", "--segment", str(segment), "--symbol", "leaf", "--json"],
    )
    callees_result = runner.invoke(
        app,
        ["graph", "callees", "--segment", str(segment), "--symbol", "root", "--json"],
    )

    assert index_result.exit_code == 0, index_result.output
    assert json.loads(index_result.output)["edge_count"] == 1
    assert [node["symbol_name"] for node in json.loads(callers_result.output)["nodes"]] == ["root"]
    assert [node["symbol_name"] for node in json.loads(callees_result.output)["nodes"]] == ["leaf"]
