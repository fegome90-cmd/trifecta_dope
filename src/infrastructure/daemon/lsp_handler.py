from typing import Any

from src.domain.lsp_contracts import FallbackReason, LSPResponse
from src.infrastructure.lsp_client import LSPState


def handle_lsp_request(req: dict[str, Any], lsp_client: Any) -> dict[str, Any]:
    """Handle JSON envelope LSP requests for daemon run."""
    method = req.get("method", "")
    params = req.get("params", {})

    if not lsp_client:
        return LSPResponse.unavailable_response(
            fallback_reason=FallbackReason.DAEMON_UNAVAILABLE,
            message="LSP client not initialized",
        ).to_dict()

    if not lsp_client.is_ready():
        return LSPResponse.degraded_response(
            fallback_reason=FallbackReason.LSP_NOT_READY,
            message=f"LSP state: {lsp_client.state.value}",
        ).to_dict()

    if lsp_client.state == LSPState.FAILED:
        return LSPResponse.degraded_response(
            fallback_reason=FallbackReason.LSP_ERROR,
            message="LSP in FAILED state",
        ).to_dict()

    # Auto-didOpen: pyright needs document open before hover/definition
    if method in ("textDocument/hover", "textDocument/definition",
                  "textDocument/references", "textDocument/completion"):
        uri = params.get("textDocument", {}).get("uri", "")
        if uri:
            from pathlib import Path as _Path
            doc_path = _Path(uri.replace("file://", ""))
            if doc_path.exists():
                lsp_client.did_open(doc_path, doc_path.read_text())

    try:
        result = lsp_client.request(method, params)
        if result:
            return LSPResponse.full_response(result).to_dict()
        return LSPResponse.degraded_response(
            fallback_reason=FallbackReason.LSP_REQUEST_TIMEOUT,
            message=f"LSP request '{method}' returned no data",
        ).to_dict()
    except Exception as exc:
        return LSPResponse.error_response(
            error_code="LSP_ERROR",
            fallback_reason=FallbackReason.LSP_ERROR,
            message=str(exc),
        ).to_dict()
