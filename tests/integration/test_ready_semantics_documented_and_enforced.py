import pytest
from unittest.mock import MagicMock, patch
from src.infrastructure.lsp_client import LSPClient, LSPState


def test_ready_semantics_is_post_initialize(tmp_path):
    """
    Tripwire: Enforce Option B (Post-Initialize READY).
    The system MUST transition to READY immediately after the 'initialized' handshake check,
    WITHOUT waiting for 'publishDiagnostics'.

    This ensures RPC availability is prioritized over semantic readiness (which is flaky without VFS).
    """
    client = LSPClient(tmp_path)
    client.process = MagicMock()
    # Mock communication
    client._send_rpc = MagicMock()

    # Mock _read_rpc sequence:
    # 1. 'initialize' response (triggers "initialized" notification + READY transition)
    # 2. EOF or irrelevant message to exit loop (simulated by side_effect exception or break)

    init_response = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}

    # We patch _read_rpc to return init_response then None (EOF)
    with patch.object(client, "_read_rpc", side_effect=[init_response, None]):
        # Run the loop logic (synchronously for test)
        client._run_loop()

    # VERIFICATION:
    # 1. State must be READY
    assert client.state == LSPState.READY, "LSPClient should be READY after initialize handshake"

    # 2. 'initialized' notification must have been sent
    # We check calls to _send_rpc
    # First call is initialize request, Second is initialized notification
    assert client._send_rpc.call_count >= 2
    args, _ = client._send_rpc.call_args_list[1]
    assert args[0]["method"] == "initialized", "Client must send 'initialized' notification"
