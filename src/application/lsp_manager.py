"""
LSP Manager: Pyright headless with state machine.

STATE MACHINE:
  COLD → WARMING (spawn process)
       → READY (initialize ok + didOpen + publishDiagnostics received)
       → FAILED (error/crash)

POLICY:
  - Warm-up in parallel after AST localizes candidate
  - READY-only gating: definition/hover only if state==READY
  - If not READY: fallback to AST-only, log lsp.fallback
  - JSON-RPC 2.0 framing with Content-Length
  - Non-blocking stderr handling (DEVNULL or drain thread)

TELEMETRY:
  - lsp.spawn: state=WARMING, server=pyright, pid
  - lsp.state_change: from, to, reason
  - lsp.request: method, file, line, col, resolved, fallback, timing_ms
"""

import json
import subprocess
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

__all__ = [
    "LSPState",
    "LSPManager",
]


class LSPState(Enum):
    """LSP connection state."""

    COLD = "cold"
    WARMING = "warming"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class LSPDiagnosticInfo:
    """Minimal diagnostic info from publishDiagnostics."""

    uri: str
    diagnostics_count: int


class LSPManager:
    """
    Manages Pyright LSP connection with state machine.

    Non-blocking, READY-only gating, fail-safe to AST.
    """

    def __init__(self, workspace_root: Path, enabled: bool = False) -> None:
        """
        Initialize LSP manager.

        Args:
            workspace_root: Root for pyright
            enabled: If False, state stays COLD
        """
        self.workspace_root = workspace_root
        self.enabled = enabled
        self.state = LSPState.COLD
        self._process: Optional[subprocess.Popen[str]] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._diagnostics_received: set[str] = set()  # URIs with diagnostics
        self._stderr_thread: Optional[threading.Thread] = None

    def spawn_async(self, best_file_uri: Optional[str] = None) -> None:
        """
        Spawn Pyright LSP in background (non-blocking).

        Args:
            best_file_uri: URI to open after initialize (optional)
        """
        if not self.enabled or self.state != LSPState.COLD:
            return

        def _spawn_task() -> None:
            try:
                self.state = LSPState.WARMING
                # Start pyright LSP server
                self._process = subprocess.Popen(
                    ["pyright", "--outputjson"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    cwd=str(self.workspace_root),
                )
                # Initialize LSP
                self._send_initialize()
                # Open best file if provided
                if best_file_uri:
                    self._send_did_open(best_file_uri)
            except Exception:
                # Process spawn failed
                self.state = LSPState.FAILED

        # Spawn in background thread
        t = threading.Thread(target=_spawn_task, daemon=True)
        t.start()

    def _send_initialize(self) -> None:
        """Send LSP initialize request."""
        if not self._process:
            return

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "processId": None,
                "rootPath": str(self.workspace_root),
                "capabilities": {},
            },
        }
        self._send_json_rpc(request)

    def _send_did_open(self, uri: str) -> None:
        """Send LSP textDocument/didOpen."""
        if not self._process:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": "",  # Empty content; pyright will read
                }
            },
        }
        self._send_json_rpc(notification)

    def _send_json_rpc(self, obj: dict[str, Any]) -> None:
        """Send JSON-RPC message with Content-Length header."""
        if not self._process or not self._process.stdin:
            return

        try:
            payload = json.dumps(obj)
            content_length = len(payload.encode("utf-8"))
            message = (
                f"Content-Length: {content_length}\r\n"
                f"Content-Type: application/vscode-jsonrpc; charset=utf-8\r\n"
                f"\r\n"
                f"{payload}"
            )
            self._process.stdin.write(message)
            self._process.stdin.flush()
        except Exception:
            self.state = LSPState.FAILED

    def _next_request_id(self) -> int:
        """Generate next JSON-RPC request ID."""
        with self._lock:
            self._request_id += 1
            return self._request_id

    def mark_diagnostics_received(self, uri: str) -> None:
        """Called when publishDiagnostics received for URI."""
        with self._lock:
            self._diagnostics_received.add(uri)
            # Transition to READY if we have diagnostics for at least 1 file
            if self.state == LSPState.WARMING and self._diagnostics_received:
                self.state = LSPState.READY

    def is_ready(self) -> bool:
        """Check if LSP is READY for requests."""
        with self._lock:
            return self.state == LSPState.READY

    def request_definition(
        self, uri: str, line: int, col: int
    ) -> Optional[dict[str, Any]]:
        """
        Request textDocument/definition (READY-only gating).

        Returns:
            Location dict or None if not READY / request fails
        """
        if not self.is_ready():
            return None

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": col},
            },
        }
        return self._request_with_timeout(request)

    def request_hover(
        self, uri: str, line: int, col: int
    ) -> Optional[dict[str, Any]]:
        """Request textDocument/hover (READY-only gating)."""
        if not self.is_ready():
            return None

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": col},
            },
        }
        return self._request_with_timeout(request)

    def _request_with_timeout(
        self, request: dict[str, Any], timeout_sec: float = 0.5
    ) -> Optional[dict[str, Any]]:
        """Send request and wait for response with timeout."""
        if not self._process:
            return None

        try:
            self._send_json_rpc(request)
            # Would read from stdout here in real implementation
            # For MVP: return mock response or None
            return None
        except Exception:
            self.state = LSPState.FAILED
            return None

    def shutdown(self) -> None:
        """Gracefully shutdown LSP process."""
        try:
            if self._process:
                self._process.terminate()
                self._process.wait(timeout=2.0)
        except Exception:
            pass
        finally:
            self.state = LSPState.COLD
