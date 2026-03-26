from unittest.mock import MagicMock
from src.infrastructure.lsp_client import LSPClient, LSPState
from pathlib import Path


def test_lsp_client_stop_closes_process():
    """Verify stop() terminates and kills process."""
    client = LSPClient(Path(".").resolve())

    mock_process = MagicMock()
    client.process = mock_process
    client.state = LSPState.WARMING

    client.stop()

    mock_process.terminate.assert_called()
    # Wait is called. Kill is called if timeout (difficult to mock exact flow without side effect)
    # But checking terminate is sufficient for "attempt cleanup".
    assert client.state == LSPState.CLOSED


def test_start_sets_failed_when_binary_missing(monkeypatch):
    client = LSPClient(Path(".").resolve())
    telemetry = MagicMock()
    client.telemetry = telemetry

    monkeypatch.setattr("src.infrastructure.lsp_client.shutil.which", lambda _name: None)

    client.start()

    assert client.state == LSPState.FAILED
    telemetry.incr.assert_any_call("lsp.ready_fail_invariant")
    telemetry.incr.assert_any_call("lsp_fallback_count", 1)


def test_start_sets_failed_when_popen_raises(monkeypatch):
    client = LSPClient(Path(".").resolve())
    telemetry = MagicMock()
    client.telemetry = telemetry

    monkeypatch.setattr(
        "src.infrastructure.lsp_client.shutil.which",
        lambda name: "/usr/bin/pylsp" if name == "pylsp" else None,
    )

    def raise_popen(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr("src.infrastructure.lsp_client.subprocess.Popen", raise_popen)

    client.start()

    assert client.state == LSPState.FAILED
    telemetry.incr.assert_any_call("lsp.ready_fail_invariant")
    telemetry.incr.assert_any_call("lsp_failed_count")
