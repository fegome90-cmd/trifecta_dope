from src.infrastructure.daemon.lsp_handler import handle_lsp_request
from src.infrastructure.lsp_client import LSPState


class FakeLSPClient:
    def __init__(self, *, ready: bool, state: LSPState, result=None, error: Exception | None = None):
        self._ready = ready
        self.state = state
        self._result = result
        self._error = error

    def is_ready(self) -> bool:
        return self._ready

    def request(self, method: str, params: dict):
        del method, params
        if self._error:
            raise self._error
        return self._result


def test_handle_lsp_request_without_client() -> None:
    response = handle_lsp_request({"method": "textDocument/definition", "params": {}}, None)

    assert response == {
        "status": "ok",
        "capability_state": "UNAVAILABLE",
        "backend": "unavailable",
        "response_state": "degraded",
        "fallback_reason": "daemon_unavailable",
        "message": "LSP client not initialized",
    }


def test_handle_lsp_request_not_ready() -> None:
    client = FakeLSPClient(ready=False, state=LSPState.WARMING)

    response = handle_lsp_request({"method": "textDocument/definition", "params": {}}, client)

    assert response["fallback_reason"] == "lsp_not_ready"
    assert response["message"] == "LSP state: WARMING"


def test_handle_lsp_request_failed_state_is_degraded() -> None:
    client = FakeLSPClient(ready=False, state=LSPState.FAILED)

    response = handle_lsp_request({"method": "textDocument/definition", "params": {}}, client)

    assert response["fallback_reason"] == "lsp_not_ready"


def test_handle_lsp_request_success() -> None:
    client = FakeLSPClient(
        ready=True,
        state=LSPState.READY,
        result={"uri": "file:///tmp/x.py", "range": {"start": {"line": 0, "character": 0}}},
    )

    response = handle_lsp_request({"method": "textDocument/definition", "params": {}}, client)

    assert response == {
        "status": "ok",
        "capability_state": "FULL",
        "backend": "lsp_pyright",
        "response_state": "complete",
        "data": {"uri": "file:///tmp/x.py", "range": {"start": {"line": 0, "character": 0}}},
    }


def test_handle_lsp_request_empty_result() -> None:
    client = FakeLSPClient(ready=True, state=LSPState.READY, result=None)

    response = handle_lsp_request({"method": "textDocument/definition", "params": {}}, client)

    assert response["fallback_reason"] == "lsp_request_timeout"
    assert response["message"] == "LSP request 'textDocument/definition' returned no data"


def test_handle_lsp_request_exception() -> None:
    client = FakeLSPClient(
        ready=True,
        state=LSPState.READY,
        error=RuntimeError("boom"),
    )

    response = handle_lsp_request({"method": "textDocument/definition", "params": {}}, client)

    assert response == {
        "status": "error",
        "capability_state": "UNAVAILABLE",
        "backend": "unavailable",
        "response_state": "error",
        "fallback_reason": "lsp_error",
        "error_code": "LSP_ERROR",
        "message": "boom",
    }
