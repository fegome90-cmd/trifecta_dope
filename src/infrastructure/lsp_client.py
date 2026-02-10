import subprocess
import json
import shutil
import threading
import os
import sys
from typing import Optional, Dict, Any
from enum import Enum
from pathlib import Path


class LSPState(Enum):
    COLD = "COLD"
    WARMING = "WARMING"
    READY = "READY"
    FAILED = "FAILED"
    CLOSED = "CLOSED"


class LSPClient:
    def __init__(self, root_path: Path, telemetry: Any = None):
        self.root_path = root_path
        self.telemetry = telemetry
        self.state = LSPState.COLD
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.lock = threading.Lock()
        self._stop_lock = threading.Lock()  # Separate lock for stop idempotency
        self.stopping = threading.Event()
        self._thread: Optional[threading.Thread] = None  # Track loop thread for join
        self._capabilities: Dict[str, Any] = {}
        self._warmup_file: Optional[Path] = None

        # Request handling
        self._next_id = 1000  # Avoid conflict with init id 1
        self._pending_requests: Dict[int, Any] = {}
        self._request_events: Dict[int, threading.Event] = {}

    def start(self) -> None:
        """Start LSP server in background."""
        with self.lock:
            if self.state != LSPState.COLD:
                return

            executable = shutil.which("pylsp") or shutil.which("pyright-langserver")
            if not executable:
                self._transition(LSPState.FAILED)
                self._log_event(
                    "lsp.spawn",
                    {"executable": None},
                    {"status": "failed", "error": "binary_not_found"},
                    0,
                )
                return

            try:
                self._transition(LSPState.WARMING)
                cmd = [executable]
                if "pyright" in executable:
                    cmd.append("--stdio")

                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=False,
                )

                if self.telemetry:
                    self.telemetry.incr("lsp_spawn_count")

                # Robust Sanitize
                exe_log = "unknown"
                try:
                    if executable:
                        exe_log = Path(executable).name
                except Exception:
                    pass

                self._log_event(
                    "lsp.spawn",
                    {"executable": exe_log},
                    {"status": "ok", "pid": self.process.pid},
                    1,
                )

                # Start handshake + Read Loop (save thread reference for join)
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

            except Exception as e:
                self._transition(LSPState.FAILED)
                if self.telemetry:
                    self.telemetry.incr("lsp_failed_count")

                # Capture stderr for debug
                err_out = "Unknown"
                if self.process:
                    try:
                        _, stderr_data = self.process.communicate(timeout=0.2)
                        if stderr_data:
                            err_out = stderr_data.decode("utf-8")
                    except Exception:
                        pass
                sys.stderr.write(f"DEBUG: LSP Start Failed: {e}. Stderr: {err_out}\n")

                # Sanitize executable path for telemetry
                exe_name = "unknown"
                if executable:
                    exe_name = Path(executable).name

                self._log_event(
                    "lsp.spawn", {"executable": exe_name}, {"status": "error", "error": str(e)}, 0
                )

    def stop(self) -> None:
        """Strict cleanup: signal -> terminate -> join thread -> close streams.

        SHUTDOWN ORDER INVARIANT (do not reorder):
          1. Set stopping flag (signal intent)
          2. Terminate process
          3. Join loop thread (wait for exit)
          4. Close streams (only after thread exits)

        Idempotent: safe to call multiple times.
        """
        with self._stop_lock:
            # 1. Signal threads first (defensive: stopping should only be set here)
            if not self.stopping.is_set():
                self.stopping.set()

            # 2. Check/set state (idempotent)
            with self.lock:
                if self.state == LSPState.CLOSED:
                    return
                self.state = LSPState.CLOSED

            # 3. Terminate process
            if self.process:
                try:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=0.2)
                except Exception:
                    pass  # Process might be gone

            # 4. Join background thread BEFORE closing streams
            # Increased timeout for CI stability (was 0.5s)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)

                # CRITICAL: If thread still alive after join, DO NOT close streams
                # This avoids write-to-closed-file race in edge cases (blocked I/O)
                # Better to leak streams in rare shutdown failure than reintroduce bug
                if self._thread.is_alive():
                    # Thread didn't terminate cleanly; leave streams open
                    # Process is already terminated, thread will eventually exit on EOF
                    return

            # 5. Close streams ONLY after thread exits
            if self.process:
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                    if self.process.stdout:
                        self.process.stdout.close()
                    if self.process.stderr:
                        self.process.stderr.close()
                except Exception:
                    pass  # Already closed

    def did_open(self, file_path: Path, content: str) -> None:
        """Notify file open to trigger diagnostics."""
        with self.lock:
            if self.state == LSPState.CLOSED or not self.process:
                return

        self._warmup_file = file_path
        msg = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": file_path.as_uri(),
                    "languageId": "python",
                    "version": 1,
                    "text": content,
                }
            },
        }
        self._send_rpc(msg)

    def is_ready(self) -> bool:
        return self.state == LSPState.READY

    def _transition(self, new_state: LSPState) -> None:
        self.state = new_state

    def _log_event(
        self, cmd: str, args: Dict[str, Any], result: Dict[str, Any], timing: int, **kwargs: Any
    ) -> None:
        if self.telemetry:
            # kwargs are passed to event as x_fields
            self.telemetry.event(cmd, args, result, timing, lsp_state=self.state.value, **kwargs)

    def _run_loop(self) -> None:
        """Handshake + Read Loop."""
        try:
            # 1. Initialize
            req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": os.getpid(),
                    "rootUri": self.root_path.as_uri(),
                    "capabilities": {},
                },
            }
            self._send_rpc(req)

            # 2. Wait for Response (blocking single read)
            resp = self._read_rpc()
            if not resp or "result" not in resp:
                self._transition(LSPState.FAILED)
                return

            self._capabilities = resp["result"].get("capabilities", {})
            self._send_rpc({"jsonrpc": "2.0", "method": "initialized", "params": {}})

            # relaxed READY: Transition immediately to allow requests
            with self.lock:
                self._transition(LSPState.READY)

            if self.telemetry:
                self.telemetry.incr("lsp_ready_count")
                self._log_event(
                    "lsp.state_change",
                    {},
                    {"status": "ready"},
                    1,
                    reason="initialized",
                )

            # 3. Read Loop (Waiting for publishDiagnostics & Responses)
            while self.state != LSPState.CLOSED:
                msg = self._read_rpc()
                if not msg:
                    break  # EOF

                # Handle Response
                if "id" in msg and "result" in msg:
                    req_id = msg["id"]
                    with self.lock:
                        if req_id in self._pending_requests:
                            self._pending_requests[req_id] = msg["result"]
                            self._request_events[req_id].set()

                # Handle Notification
                method = msg.get("method", "")
                if method == "textDocument/publishDiagnostics":
                    # Log diagnostics but do not control state (already READY)
                    pass
        except Exception as e:
            # If we're stopping, silently exit without printing debug messages
            if self.stopping.is_set():
                return

            # Only log errors if NOT intentionally stopping
            # Capture stderr
            err_out = "Unknown"
            if self.process:
                try:
                    _, stderr_data = self.process.communicate(timeout=0.2)
                    if stderr_data:
                        err_out = stderr_data.decode("utf-8")
                except Exception:
                    pass
            sys.stderr.write(f"DEBUG: LSP Loop Exception: {e}. Stderr: {err_out}\n")
            self._transition(LSPState.FAILED)

    def request(
        self, method: str, params: Dict[str, Any], timeout: float = 2.0
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for the response."""
        with self.lock:
            if self.state != LSPState.READY:
                return None

            req_id = self._next_id
            self._next_id += 1
            event = threading.Event()
            self._pending_requests[req_id] = None  # Placeholder
            self._request_events[req_id] = event

        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        self._send_rpc(msg)

        # Wait for response
        if event.wait(timeout):
            with self.lock:
                result = self._pending_requests.pop(req_id, None)
                self._request_events.pop(req_id, None)
                # Type guard for mypy
                return result if isinstance(result, dict) else None
        else:
            with self.lock:
                self._pending_requests.pop(req_id, None)
                self._request_events.pop(req_id, None)
                return None  # Timeout

    def _send_rpc(self, msg: Dict[str, Any]) -> None:
        # Don't attempt writes if stopping
        if self.stopping.is_set():
            return
        if not self.process or not self.process.stdin:
            return
        try:
            content = json.dumps(msg).encode("utf-8")
            header = f"Content-Length: {len(content)}\r\n\r\n".encode("ascii")
            self.process.stdin.write(header + content)
            self.process.stdin.flush()
        except (OSError, ValueError, BrokenPipeError):
            # Silently ignore write errors during shutdown
            pass

    def _read_rpc(self) -> Optional[Dict[str, Any]]:
        if not self.process or not self.process.stdout:
            return None
        try:
            # Read Headers
            length = None
            while True:
                line = self.process.stdout.readline()
                if not line:
                    if length is None:
                        # EOF before any headers
                        return None
                    # EOF inside headers? Break and try reading content?
                    break

                line = line.strip()
                if not line:
                    # End of headers
                    break

                if line.startswith(b"Content-Length: "):
                    length = int(line.split(b": ")[1])

            if length is None:
                return None

            # Read Content
            content = b""
            while len(content) < length:
                chunk = self.process.stdout.read(length - len(content))
                if not chunk:
                    break
                content += chunk

            # Parse JSON
            try:
                msg = json.loads(content.decode("utf-8"))
                # Type guard for mypy
                return msg if isinstance(msg, dict) else None
            except json.JSONDecodeError:
                return None
        except Exception:
            return None
