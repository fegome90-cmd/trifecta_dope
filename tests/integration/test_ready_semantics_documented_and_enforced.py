from unittest.mock import MagicMock, patch
from src.infrastructure.lsp_client import (
    LSPClient,
    LSPState,
    INVARIANT_PROCESS_ALIVE,
    INVARIANT_WORKSPACE_ROOT,
    INVARIANT_HEALTH_CHECK,
)


def test_ready_semantics_is_post_initialize(tmp_path):
    client = LSPClient(tmp_path)
    client.process = MagicMock()
    client._capabilities = {}
    client._send_rpc = MagicMock()

    init_response = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}

    with patch.object(client, "_read_rpc", side_effect=[init_response, None]):
        with patch.object(client, "_check_invariants", return_value=True):
            client._run_loop()

    assert client.state == LSPState.READY, "LSPClient should be READY after initialize handshake"

    assert client._send_rpc.call_count >= 2
    args, _ = client._send_rpc.call_args_list[1]
    assert args[0]["method"] == "initialized", "Client must send 'initialized' notification"


def test_ready_fails_when_invariants_fail(tmp_path):
    client = LSPClient(tmp_path)
    client.process = None
    client._capabilities = {}
    client._send_rpc = MagicMock()

    init_response = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}

    with patch.object(client, "_read_rpc", side_effect=[init_response, None]):
        client._run_loop()

    assert client.state == LSPState.FAILED, "LSPClient should be FAILED when invariants fail"
    assert len(client.get_failed_invariants()) > 0, "Failed invariants should be recorded"


def test_invariant_check_tracks_failures(tmp_path):
    client = LSPClient(tmp_path)

    client._verify_process_alive()
    assert INVARIANT_PROCESS_ALIVE in client._failed_invariants

    client._failed_invariants.clear()
    client.root_path = tmp_path / "nonexistent"
    client._verify_workspace_root()
    assert INVARIANT_WORKSPACE_ROOT in client._failed_invariants

    client._failed_invariants.clear()
    client._capabilities = {}
    client._verify_health_check()
    assert INVARIANT_HEALTH_CHECK in client._failed_invariants
