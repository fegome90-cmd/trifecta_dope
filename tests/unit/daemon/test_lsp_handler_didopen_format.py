"""Regression test: didOpen must transform daemon params to LSP format.

This test verifies that handle_lsp_request() correctly transforms
the daemon's didOpen params (path, content) into the LSP format
(textDocument.uri, textDocument.languageId, textDocument.version, textDocument.text)
before sending to pyright.

See: docs/daemon-lsp-scope/daemon_lsp_operationalization_plan_v2.md
"""

from pathlib import Path
from unittest.mock import MagicMock

from src.infrastructure.daemon.lsp_handler import handle_lsp_request
from src.infrastructure.lsp_client import LSPState


def test_didopen_transforms_daemon_params_to_lsp_format(tmp_path: Path) -> None:
    """Verify didOpen transforms daemon params to LSP textDocument format."""
    mock_client = MagicMock()
    mock_client.state = LSPState.READY
    mock_client.is_ready.return_value = True

    test_file = tmp_path / "test.py"
    test_file.write_text("def hello(): pass")
    content = test_file.read_text()

    req = {
        "method": "textDocument/didOpen",
        "params": {"path": str(test_file), "content": content},
    }

    result = handle_lsp_request(req, mock_client)

    # Verify response is notification_sent
    assert result["status"] == "ok"
    assert result["data"]["status"] == "notification_sent"

    # Verify _send_rpc was called with LSP format
    mock_client._send_rpc.assert_called_once()
    sent_msg = mock_client._send_rpc.call_args[0][0]

    assert sent_msg["jsonrpc"] == "2.0"
    assert sent_msg["method"] == "textDocument/didOpen"

    text_doc = sent_msg["params"]["textDocument"]
    assert text_doc["uri"] == test_file.resolve().as_uri()
    assert text_doc["languageId"] == "python"
    assert text_doc["version"] == 1
    assert text_doc["text"] == content


def test_didopen_detects_language_from_extension(tmp_path: Path) -> None:
    """Verify language detection from file extension."""
    mock_client = MagicMock()
    mock_client.state = LSPState.READY
    mock_client.is_ready.return_value = True

    for ext, expected_lang in [
        (".py", "python"),
        (".js", "javascript"),
        (".ts", "typescript"),
        (".txt", "plaintext"),
    ]:
        test_file = tmp_path / f"test{ext}"
        test_file.write_text("content")

        req = {
            "method": "textDocument/didOpen",
            "params": {"path": str(test_file), "content": "content"},
        }

        handle_lsp_request(req, mock_client)

        sent_msg = mock_client._send_rpc.call_args[0][0]
        assert sent_msg["params"]["textDocument"]["languageId"] == expected_lang
        mock_client.reset_mock()


def test_didopen_ignores_markdown_files(tmp_path: Path) -> None:
    """Verify that .md files are ignored and do not trigger _send_rpc."""
    mock_client = MagicMock()
    mock_client.state = LSPState.READY
    mock_client.is_ready.return_value = True

    test_file = tmp_path / "test.md"
    test_file.write_text("# Hello World")

    req = {
        "method": "textDocument/didOpen",
        "params": {"path": str(test_file), "content": "# Hello World"},
    }

    result = handle_lsp_request(req, mock_client)

    # Verify response is ok but notes it's ignored
    assert result["status"] == "ok"
    assert result["data"]["status"] == "notification_sent"
    assert "ignored_extension=.md" in result["data"].get("note", "")

    # Verify _send_rpc was NOT called
    mock_client._send_rpc.assert_not_called()