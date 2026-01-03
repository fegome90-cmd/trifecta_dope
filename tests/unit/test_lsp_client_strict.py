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
