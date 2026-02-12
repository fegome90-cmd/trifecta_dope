from __future__ import annotations

import json

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def test_ast_snippet_is_explicitly_not_implemented() -> None:
    result = runner.invoke(app, ["ast", "snippet", "sym://python/mod/src.domain.result"])
    assert result.exit_code != 0, result.stdout

    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error_code"] == "NOT_IMPLEMENTED"
    assert "ast snippet" in payload["message"].lower()
    assert "hint" in payload
    assert payload["context"]["command"] == "ast.snippet"
    assert payload["context"]["uri"] == "sym://python/mod/src.domain.result"


def test_ast_hover_exposes_wip_stub_contract() -> None:
    result = runner.invoke(
        app,
        ["ast", "hover", "src/infrastructure/cli.py", "--line", "10", "--char", "1"],
    )
    assert result.exit_code == 0, result.stdout

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["kind"] == "skeleton"
    assert payload["backend"] == "wip_stub"
    assert payload["capability_state"] == "WIP"
    assert payload["response_state"] == "partial"
