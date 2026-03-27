from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.lsp_client import LSPClient, LSPState


def test_lsp_client_stop_closes_process() -> None:
    """Verify stop() terminates and kills process."""
    client = LSPClient(Path(".").resolve())

    mock_process = MagicMock()
    client.process = mock_process
    client.state = LSPState.WARMING

    client.stop()

    mock_process.terminate.assert_called()
    assert client.state == LSPState.CLOSED


@pytest.mark.parametrize(
    ("env_value", "expected_timeout"),
    [(None, 30.0), ("7", 7.0), ("2.5", 2.5), ("invalid", 30.0)],
)
def test_request_uses_timeout_from_env_when_timeout_is_none(
    monkeypatch: pytest.MonkeyPatch,
    env_value: str | None,
    expected_timeout: float,
) -> None:
    client = LSPClient(Path(".").resolve())
    client.state = LSPState.READY
    client.process = MagicMock()
    client.process.stdin = MagicMock()

    if env_value is None:
        monkeypatch.delenv("TRIFECTA_LSP_REQUEST_TIMEOUT", raising=False)
    else:
        monkeypatch.setenv("TRIFECTA_LSP_REQUEST_TIMEOUT", env_value)

    mock_event = MagicMock()
    mock_event.wait.return_value = False

    with patch("src.infrastructure.lsp_client.threading.Event", return_value=mock_event):
        result = client.request("textDocument/hover", {}, timeout=None)

    assert result is None
    mock_event.wait.assert_called_once_with(expected_timeout)


def test_request_debug_logs_are_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    client = LSPClient(Path(".").resolve())
    client.state = LSPState.READY
    client.process = MagicMock()
    client.process.stdin = MagicMock()

    mock_event = MagicMock()

    def complete_request(_timeout: float) -> bool:
        client._pending_requests[1000] = {"contents": "ok"}
        return True

    mock_event.wait.side_effect = complete_request

    monkeypatch.delenv("TRIFECTA_LSP_DEBUG", raising=False)

    with patch("src.infrastructure.lsp_client.threading.Event", return_value=mock_event):
        result = client.request("textDocument/hover", {}, timeout=1.0)

    captured = capsys.readouterr()
    assert result == {"contents": "ok"}
    assert "[LSP_REQ_" not in captured.err


def test_request_debug_logs_are_enabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    client = LSPClient(Path(".").resolve())
    client.state = LSPState.READY
    client.process = MagicMock()
    client.process.stdin = MagicMock()

    mock_event = MagicMock()

    def complete_request(_timeout: float) -> bool:
        client._pending_requests[1000] = {"contents": "ok"}
        return True

    mock_event.wait.side_effect = complete_request

    monkeypatch.setenv("TRIFECTA_LSP_DEBUG", "1")

    with patch("src.infrastructure.lsp_client.threading.Event", return_value=mock_event):
        client.request("textDocument/hover", {}, timeout=1.0)

    captured = capsys.readouterr()
    assert "[LSP_REQ_SENT]" in captured.err


def test_send_rpc_returns_false_when_transport_unavailable() -> None:
    client = LSPClient(Path(".").resolve())

    assert client._send_rpc({"jsonrpc": "2.0"}) is False


def test_send_rpc_returns_false_when_stopping() -> None:
    client = LSPClient(Path(".").resolve())
    client.stopping.set()
    client.process = MagicMock()
    client.process.stdin = MagicMock()

    assert client._send_rpc({"jsonrpc": "2.0"}) is False


def test_send_rpc_returns_true_on_success() -> None:
    client = LSPClient(Path(".").resolve())
    client.process = MagicMock()
    client.process.stdin = MagicMock()

    assert client._send_rpc({"jsonrpc": "2.0", "method": "initialized", "params": {}}) is True
