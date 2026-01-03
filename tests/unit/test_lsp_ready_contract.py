"""
Tripwire Test: LSP Request Ready Contract
See: docs/contracts/LSP_RELAXED_READY.md

This test strictly verifies that the LSPClient transitions to the READY state
immediately after a successful 'initialize' handshake, without waiting for
'publishDiagnostics' or other notifications.
"""

from pathlib import Path
from unittest.mock import patch
from src.infrastructure.lsp_client import LSPClient, LSPState


def test_contract_relaxed_ready_immediate():
    """
    Contract: Relaxed READY
    Goal: Verify that client is READY essentially immediately after initialization.
    """
    # Use absolute path to avoid URI issues
    client = LSPClient(Path(".").resolve())

    # Mock the RPC read sequence for a minimal successful handshake:
    # 1. Response to 'initialize' request
    init_resp = {"result": {"capabilities": {}}}
    # 2. Some other notification (optional, but realistic)
    other_notif = {"method": "telemetry/event", "params": {}}
    # 3. None to break the read loop
    mock_reads = [init_resp, other_notif, None]

    with (
        patch.object(client, "_read_rpc", side_effect=mock_reads),
        patch.object(client, "_send_rpc") as mock_send,
    ):
        # Direct call to _run_loop to bypass threading for unit test
        client._run_loop()

        # Contract Assertion:
        # The client MUST be in the READY state after the handshake.
        assert client.state == LSPState.READY, (
            "Violation of Relaxed READY contract: Client did not transition to READY "
            "after initialization."
        )

        # Optional: Verify that 'initialized' notification was sent
        # Filter calls to check for "initialized" method
        initialized_calls = [
            call for call in mock_send.call_args_list if call[0][0].get("method") == "initialized"
        ]
        assert len(initialized_calls) > 0, "Client must send 'initialized' notification"
