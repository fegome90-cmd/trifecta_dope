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


def test_ast_hover_exposes_unavailable_contract() -> None:
    from unittest import mock
    with mock.patch.dict("os.environ", {"PATH": ""}):
        result = runner.invoke(
            app,
            ["ast", "hover", "src/infrastructure/cli.py", "--line", "10", "--char", "1"],
        )
        assert result.exit_code == 0, result.stdout

        payload = json.loads(result.stdout)
        assert payload["status"] == "ok"
        assert payload["backend"] == "unavailable"
        assert payload["capability_state"] == "UNAVAILABLE"
        assert payload["response_state"] == "degraded"
        assert "fallback_reason" in payload
