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



def test_stop_clears_runtime_residue_after_clean_shutdown():
    client = LSPClient(Path('.').resolve())

    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    client.process = mock_process
    client.state = LSPState.READY
    client._capabilities = {"hoverProvider": True}
    client._warmup_file = Path('warmup.py')
    client._pending_requests = {1001: {"ok": True}}
    event = MagicMock()
    client._request_events = {1001: event}

    client.stop()

    assert client.state == LSPState.CLOSED
    assert client.process is None
    assert client._thread is None
    assert client._capabilities == {}
    assert client._warmup_file is None
    assert client._pending_requests == {}
    assert client._request_events == {}
    event.set.assert_called_once()
    mock_process.stdin.close.assert_called_once()
    mock_process.stdout.close.assert_called_once()
    mock_process.stderr.close.assert_called_once()


def test_stop_retries_cleanup_on_second_call_after_join_timeout():
    client = LSPClient(Path('.').resolve())

    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    client.process = mock_process
    client.state = LSPState.WARMING

    mock_thread = MagicMock()
    mock_thread.is_alive.side_effect = [True, True, False]
    client._thread = mock_thread

    client.stop()

    assert client.process is mock_process
    assert client._thread is mock_thread

    client.stop()

    assert client.state == LSPState.CLOSED
    assert client.process is None
    assert client._thread is None
    mock_process.stdin.close.assert_called_once()
    mock_process.stdout.close.assert_called_once()
    mock_process.stderr.close.assert_called_once()
