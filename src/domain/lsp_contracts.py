"""LSP Response Contracts - Explicit Fallback Protocol.

This module defines the contract for LSP responses with explicit fallback handling.
No silent fallbacks allowed - every degraded response must declare its state.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


class CapabilityState(str, Enum):
    """Capability state of the LSP response."""

    FULL = "FULL"  # LSP fully operational, real data
    DEGRADED = "DEGRADED"  # Fallback to AST/limited functionality
    WIP = "WIP"  # Work in progress, not fully implemented
    UNAVAILABLE = "UNAVAILABLE"  # LSP not available


class FallbackReason(str, Enum):
    """Reason for fallback to degraded mode."""

    LSP_NOT_READY = "lsp_not_ready"  # LSP warming or failed
    LSP_BINARY_NOT_FOUND = "lsp_binary_not_found"  # pyright/pylsp not installed
    LSP_REQUEST_TIMEOUT = "lsp_request_timeout"  # Request timed out
    LSP_NOT_IMPLEMENTED = "lsp_not_implemented"  # Feature not yet implemented
    LSP_ERROR = "lsp_error"  # LSP returned error
    DAEMON_UNAVAILABLE = "daemon_unavailable"  # LSP daemon not running


class ResponseState(str, Enum):
    """State of the response itself."""

    COMPLETE = "complete"  # Full response with all data
    PARTIAL = "partial"  # Partial data (fallback)
    ERROR = "error"  # Error occurred
    DEGRADED = "degraded"  # Explicitly degraded


class Backend(str, Enum):
    """Backend that served the response."""

    LSP_PYRIGHT = "lsp_pyright"  # Real LSP via pyright
    LSP_PYLSP = "lsp_pylsp"  # Real LSP via pylsp
    AST_ONLY = "ast_only"  # AST-only fallback
    WIP_STUB = "wip_stub"  # WIP implementation stub
    UNAVAILABLE = "unavailable"  # No backend available


@dataclass
class LSPResponse:
    """Standard LSP response structure with explicit fallback contract.

    Every response must include:
    - capability_state: Actual capability state
    - fallback_reason: Why degraded (if applicable)
    - backend: What served the response
    - response_state: State of this response

    No silent fallbacks allowed.
    """

    status: str  # "ok" or "error"
    capability_state: str  # CapabilityState value
    backend: str  # Backend value
    response_state: str  # ResponseState value
    fallback_reason: Optional[str] = None  # FallbackReason value, required if degraded
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None  # Required if status == "error"
    message: Optional[str] = None  # Human readable, optional

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Remove None values for cleaner JSON
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def full_response(
        cls,
        data: Dict[str, Any],
        backend: Backend = Backend.LSP_PYRIGHT,
    ) -> "LSPResponse":
        """Create a full LSP response."""
        return cls(
            status="ok",
            capability_state=CapabilityState.FULL.value,
            backend=backend.value,
            response_state=ResponseState.COMPLETE.value,
            data=data,
        )

    @classmethod
    def degraded_response(
        cls,
        fallback_reason: FallbackReason,
        backend: Backend = Backend.AST_ONLY,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> "LSPResponse":
        """Create an explicit degraded response."""
        return cls(
            status="ok",
            capability_state=CapabilityState.DEGRADED.value,
            backend=backend.value,
            response_state=ResponseState.DEGRADED.value,
            fallback_reason=fallback_reason.value,
            data=data,
            message=message,
        )

    @classmethod
    def wip_response(
        cls,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = "Work in progress",
    ) -> "LSPResponse":
        """Create a WIP response."""
        return cls(
            status="ok",
            capability_state=CapabilityState.WIP.value,
            backend=Backend.WIP_STUB.value,
            response_state=ResponseState.PARTIAL.value,
            fallback_reason=FallbackReason.LSP_NOT_IMPLEMENTED.value,
            data=data,
            message=message,
        )

    @classmethod
    def error_response(
        cls,
        error_code: str,
        fallback_reason: FallbackReason,
        message: str,
        backend: Backend = Backend.UNAVAILABLE,
    ) -> "LSPResponse":
        """Create a fail-closed error response.

        Use this when the operation requires LSP and cannot fallback.
        """
        return cls(
            status="error",
            capability_state=CapabilityState.UNAVAILABLE.value,
            backend=backend.value,
            response_state=ResponseState.ERROR.value,
            fallback_reason=fallback_reason.value,
            error_code=error_code,
            message=message,
        )

    @classmethod
    def unavailable_response(
        cls,
        fallback_reason: FallbackReason = FallbackReason.LSP_BINARY_NOT_FOUND,
        message: Optional[str] = None,
    ) -> "LSPResponse":
        """Create an unavailable response when LSP is not accessible."""
        return cls(
            status="ok",
            capability_state=CapabilityState.UNAVAILABLE.value,
            backend=Backend.UNAVAILABLE.value,
            response_state=ResponseState.DEGRADED.value,
            fallback_reason=fallback_reason.value,
            message=message or "LSP backend unavailable",
        )
