import pytest
import json
from typer.testing import CliRunner
from src.infrastructure.cli_ast import ast_app as app
from src.domain.ast_models import ASTResponse, ChildSymbol

runner = CliRunner()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temp workspace."""
    d = tmp_path / "workspace"
    d.mkdir()
    return d


class TestASTPhase2aStrict:
    def test_skeleton_children_structured(self, temp_workspace):
        """Verify mod skeleton returns structured ChildSymbol objects."""
        (temp_workspace / "pkg").mkdir()
        (temp_workspace / "pkg" / "__init__.py").write_text(
            "class Exposed:\n    pass\ndef f():\n    pass"
        )

        # Test mod/pkg
        res = runner.invoke(app, ["symbols", "sym://python/mod/pkg", "-s", str(temp_workspace)])
        assert res.exit_code == 0
        data = ASTResponse.model_validate_json(res.stdout)

        assert data.status == "ok"
        assert len(data.data.children) >= 2

        # Verify first child is structured
        child = data.data.children[0]
        assert isinstance(child, ChildSymbol)
        assert child.name in ("Exposed", "f")
        assert child.kind in ("class", "function")
        # Range should be >0
        assert child.range.start_line > 0
        assert child.range.end_line >= child.range.start_line

    def test_uri_roundtrip_exact(self, temp_workspace):
        """Verify URI in output exactly matches input."""
        uri = "sym://python/mod/pkg"
        (temp_workspace / "pkg.py").write_text("x=1")
        res = runner.invoke(app, ["symbols", uri, "-s", str(temp_workspace)])
        data = ASTResponse.model_validate_json(res.stdout)
        assert data.data.uri == uri

    def test_telemetry_event_shape_and_no_abs_paths(self, temp_workspace):
        """Verify telemetry events (x payload) and relative paths."""
        (temp_workspace / "pkg.py").write_text("class Foo: pass")

        # Use full telemetry to enable event logging

        res = runner.invoke(
            app,
            ["symbols", "sym://python/mod/pkg", "-s", str(temp_workspace), "--telemetry", "full"],
        )
        assert res.exit_code == 0

        # Check events.jsonl
        telemetry_dir = temp_workspace / "_ctx" / "telemetry"
        events_file = next(telemetry_dir.glob("events*.jsonl"))
        assert events_file.exists()

        events = [json.loads(line) for line in events_file.read_text().splitlines()]

        # Check selector.resolve
        resolve_ev = next(e for e in events if e["cmd"] == "selector.resolve")
        assert "x" in resolve_ev
        assert resolve_ev["x"]["resolved"] is True
        assert resolve_ev["x"]["file"] == "pkg.py"  # Relative!
        assert "matches" in resolve_ev["x"]

        # Check file.read
        read_ev = next(e for e in events if e["cmd"] == "file.read")
        assert read_ev["x"]["file"] == "pkg.py"
        assert read_ev["x"]["bytes"] > 0
        assert read_ev["x"]["mode"] in ("raw", "excerpt")
        assert read_ev["timing_ms"] > 0  # Real timing required

        # Check ast.parse
        parse_ev = next(e for e in events if e["cmd"] == "ast.parse")
        assert parse_ev["x"]["file"] == "pkg.py"
        assert parse_ev["x"]["symbols_count"] >= 1
        assert "cache_hit" in parse_ev["x"]
        assert "skeleton_bytes" in parse_ev["x"]
        assert "content_sha8" in parse_ev["x"]
        assert parse_ev["timing_ms"] > 0  # Real timing required

    def test_budget_exceeded_is_hard_error(self, temp_workspace):
        """Verify hard error when response exceeds budget."""
        # Force a large response by mocking or creating large file symbols
        # Actually easier to use a snippet with forced large output if possible,
        # or monkeypatch MAX_RESPONSE_BYTES constant locally if I could.
        # But I can create a file that generates HUGE AST?
        # Alternatively, create many symbols.

        code = "\n".join([f"def f_{i}(): pass" for i in range(5000)])  # ~100KB maybe?
        (temp_workspace / "huge.py").write_text(code)

        # 5000 lines * approx 20 bytes per ChildSymbol (json) ~= 100KB?
        # ChildSymbol: {"name":"f_0000","kind":"function","range":...} ~ 80 bytes.
        # 5000 * 80 = 400KB. Expect budget exceeded (100KB limit).

        res = runner.invoke(app, ["symbols", "sym://python/mod/huge", "-s", str(temp_workspace)])

        # Should return strict JSON with error
        data = ASTResponse.model_validate_json(res.stdout)
        assert data.status == "error"
        assert data.errors[0].code == "BUDGET_EXCEEDED"

    def test_resolution_ambiguity_fail_closed(self, temp_workspace):
        """Verify strict ambiguity error for .py vs __init__.py."""
        (temp_workspace / "ambiguous").mkdir()
        (temp_workspace / "ambiguous.py").write_text("# conflict")
        (temp_workspace / "ambiguous" / "__init__.py").write_text("# conflict")

        res = runner.invoke(
            app, ["symbols", "sym://python/mod/ambiguous", "-s", str(temp_workspace)]
        )
        assert res.exit_code == 0
        data = ASTResponse.model_validate_json(res.stdout)

        assert data.status == "error"
        assert data.errors[0].code == "AMBIGUOUS_SYMBOL"
        assert len(data.errors[0].details["candidates"]) == 2

    def test_budget_truncation_metadata(self, temp_workspace):
        """Verify strict truncation metadata (true, reason) when limits exceeded."""
        code = "\n".join([f"line_{i} = {i}" for i in range(2000)])  # ~20KB > 2KB
        (temp_workspace / "long.py").write_text(code + "\ndef f(): pass")

        # Snippet for f should be small, but file read usage is large
        # Wait, snippet logic reads full file content then slices?
        # Yes, standard AST impl might read file.
        # But truncation logic checks snippet size. To trigger truncation, snippet must be large.

        # Create a large function
        large_func = "def big_func():\n" + "\n".join([f"    var_{i} = {i}" for i in range(1200)])
        (temp_workspace / "large_snippet.py").write_text(large_func)

        res = runner.invoke(
            app, ["snippet", "sym://python/type/large_snippet/big_func", "-s", str(temp_workspace)]
        )
        assert res.exit_code == 0

        data = ASTResponse.model_validate_json(res.stdout)
        assert data.data.truncated is True
        assert data.data.truncated_reason is not None
        assert (
            "max_lines" in data.data.truncated_reason
            or "max_snippet_bytes" in data.data.truncated_reason
        )

    def test_error_shape_is_strict(self, temp_workspace):
        """Verify that error responses strictly strictly include all standard keys (data=null)."""
        # Trigger an error (e.g. symbol not found)
        res = runner.invoke(
            app, ["symbols", "sym://python/mod/nonexistent", "-s", str(temp_workspace)]
        )

        # We process stdout as strict JSON
        assert res.exit_code == 0  # Command itself doesn't crash, returns error JSON

        j = json.loads(res.stdout)
        assert j["status"] == "error"
        assert j["kind"] == "skeleton"  # default
        assert "data" in j
        assert j["data"] is None
        assert "refs" in j
        assert j["refs"] == []
        assert "next_actions" in j
        assert j["next_actions"] == []
        assert "errors" in j
        assert len(j["errors"]) > 0
        assert j["errors"][0]["code"] == "SYMBOL_NOT_FOUND"
