import json
from pathlib import Path

from typer.testing import CliRunner

from src.domain.segment_resolver import resolve_segment_ref
from src.infrastructure.graph_store import GraphStore
from src.infrastructure.cli import app


runner = CliRunner()


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
    segment_ref = resolve_segment_ref(segment)
    db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)

    assert status_result.exit_code == 0, status_result.output
    assert status_output["status"] == "ok"
    assert status_output["exists"] is False
    assert status_output["last_indexed_at"] is None
    assert not db_path.exists()


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


def test_graph_cli_callers_fail_closed_on_ambiguous_symbol(tmp_path: Path) -> None:
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
    callers_result = runner.invoke(
        app,
        ["graph", "callers", "--segment", str(segment), "--symbol", "helper", "--json"],
    )

    assert index_result.exit_code == 0, index_result.output
    assert callers_result.exit_code != 0
    payload = json.loads(callers_result.output)
    assert payload["status"] == "error"
    assert payload["error"] == "ambiguous_symbol"
    assert payload["symbol"] == "helper"
    assert [candidate["file_rel"] for candidate in payload["candidates"]] == [
        "src/pkg/first.py",
        "src/pkg/second.py",
    ]
