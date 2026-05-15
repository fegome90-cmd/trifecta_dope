"""Hybrid CLI dispatcher stub.

This module is a placeholder for the MCP-based hybrid dispatch layer.
When implemented, it will bridge trifecta commands to external MCP tools
(e.g., Paperclip, Linear) via a unified dispatcher interface.

Until the full implementation lands, this stub returns Err(...) on every
call so that callers gracefully fall through to their fallback paths.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.result import Err, Result


class HybridDispatcher:
    """Stub dispatcher — always returns Err so callers fall back."""

    def __init__(self, root: Path) -> None:  # noqa: ARG002
        pass

    def call_tool(self, tool: str, params: dict) -> Result[str, str]:
        """Return Err so the caller falls through to the normal path."""
        return Err(f"Hybrid dispatch not yet implemented for tool={tool}")
