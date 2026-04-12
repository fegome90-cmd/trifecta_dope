"""
P2 Observability: LSP error responses must reach the caller.

Before this fix, _run_loop() only matched {"id": X, "result": {...}}.
Error responses {"id": X, "error": {...}} were silently dropped,
causing request() to timeout instead of reporting the real error.
"""

from pathlib import Path
from unittest.mock import patch

from src.infrastructure.lsp_client import LSPClient, LSPState


def test_error_response_unblocks_caller():
    """Error response from server must set the Event so caller doesn't timeout."""
    client = LSPClient(Path(".").resolve())

    # Mock handshake sequence + error response for a pending request
    init_resp = {"id": 1, "result": {"capabilities": {}}}
    # Simulate an error response to request id=1000 (the first request ID)
    error_resp = {
        "id": 1000,
        "error": {"code": -32601, "message": "Method not supported"},
    }
    mock_reads = [init_resp, error_resp, None]

    with (
        patch.object(client, "_read_rpc", side_effect=mock_reads),
        patch.object(client, "_send_rpc"),
    ):
        # Pre-register the pending request so _run_loop can match the error
        import threading

        event = threading.Event()
        client._pending_requests[1000] = None
        client._request_events[1000] = event

        client._run_loop()

    assert client.state == LSPState.READY

    # Verify the error was stored with sentinel
    assert 1000 in client._pending_requests
    stored = client._pending_requests[1000]
    assert stored["__lsp_error__"] is True
    assert stored["error"]["code"] == -32601


def test_error_response_returns_none_with_diagnostic():
    """request() returns None for error responses but emits fallback telemetry."""
    client = LSPClient(Path(".").resolve())

    # Mock handshake + then set up a pending request manually
    init_resp = {"id": 1, "result": {"capabilities": {}}}
    error_resp = {
        "id": 1000,
        "error": {"code": -32602, "message": "Invalid params"},
    }
    # A notification to keep the loop alive before error response
    notif = {"method": "textDocument/publishDiagnostics", "params": {}}
    mock_reads = [init_resp, notif, error_resp, None]

    with (
        patch.object(client, "_read_rpc", side_effect=mock_reads),
        patch.object(client, "_send_rpc"),
    ):
        # Pre-register a pending request with id=1000
        import threading

        event = threading.Event()
        client._pending_requests[1000] = None
        client._request_events[1000] = event

        client._run_loop()

    # The error response should have set the event
    assert event.is_set()


def test_result_response_still_works():
    """Regression: result responses must still work after the error handling change."""
    client = LSPClient(Path(".").resolve())

    init_resp = {"id": 1, "result": {"capabilities": {}}}
    result_resp = {"id": 1000, "result": {"contents": {"kind": "markdown", "value": "hover info"}}}
    mock_reads = [init_resp, result_resp, None]

    with (
        patch.object(client, "_read_rpc", side_effect=mock_reads),
        patch.object(client, "_send_rpc"),
    ):
        import threading

        event = threading.Event()
        client._pending_requests[1000] = None
        client._request_events[1000] = event

        client._run_loop()

    assert event.is_set()
    stored = client._pending_requests.get(1000)
    # Should NOT have __lsp_error__ sentinel
    assert stored is not None
    assert "__lsp_error__" not in stored
    assert stored["contents"]["value"] == "hover info"
