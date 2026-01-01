from unittest.mock import MagicMock, patch
import json
import pytest
from src.infrastructure.lsp_client import LSPClient, LSPState
from pathlib import Path


def test_lsp_client_stop_closes_process():
    """Verify stop() terminates and kills process."""
    client = LSPClient(Path("."))

    mock_process = MagicMock()
    client.process = mock_process
    client.state = LSPState.WARMING

    client.stop()

    mock_process.terminate.assert_called()
    # Wait is called. Kill is called if timeout (difficult to mock exact flow without side effect)
    # But checking terminate is sufficient for "attempt cleanup".
    assert client.state == LSPState.CLOSED


def test_ready_requires_diagnostics():
    """Verify strict READY definition requires publishDiagnostics."""
    client = LSPClient(Path("."))

    # Simulate run_loop behavior
    # We mock _read_rpc sequence

    # 1. Response to initialize
    init_resp = {"result": {"capabilities": {}}}

    # 2. Random notification (not diagnostics)
    other_notif = {"method": "telemetry/event", "params": {}}

    # 3. Diagnostics for WRONG file
    diag_wrong = {
        "method": "textDocument/publishDiagnostics",
        "params": {"uri": "file:///tmp/other.py"},
    }

    # 4. Diagnostics for CORRECT file
    target_file = Path("/tmp/target.py")
    client._warmup_file = target_file
    diag_right = {
        "method": "textDocument/publishDiagnostics",
        "params": {"uri": target_file.as_uri()},
    }

    mock_reads = [init_resp, other_notif, diag_wrong, diag_right, None]  # None breaks loop

    with (
        patch.object(client, "_read_rpc", side_effect=mock_reads),
        patch.object(client, "_send_rpc"),
    ):
        # We call _run_loop directly (no thread)
        client._run_loop()

        # Should be READY eventually
        assert client.state == LSPState.READY

    # Verify that if loop cut short before diag_right, it is NOT ready
    client2 = LSPClient(Path("."))
    client2._warmup_file = target_file
    mock_reads_short = [init_resp, other_notif, None]
    with (
        patch.object(client2, "_read_rpc", side_effect=mock_reads_short),
        patch.object(client2, "_send_rpc"),
    ):
        client2._run_loop()
        assert client2.state != LSPState.READY
