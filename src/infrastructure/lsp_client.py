import subprocess
import json
import time
import shutil
import threading
import os
import signal
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
        self.process: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()
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
                self._log_event(
                    "lsp.spawn",
                    {"executable": executable},
                    {"status": "ok", "pid": self.process.pid},
                    1,
                )

                # Start handshake + Read Loop
                threading.Thread(target=self._run_loop, daemon=True).start()

            except Exception as e:
                self._transition(LSPState.FAILED)
                if self.telemetry:
                    self.telemetry.incr("lsp_failed_count")
                # Sanitize executable path for telemetry
                exe_name = Path(executable).name
                self._log_event(
                    "lsp.spawn", {"executable": exe_name}, {"status": "error", "error": str(e)}, 0
                )

    def stop(self) -> None:
        """Strict cleanup: terminate -> wait -> kill."""
        with self.lock:
            if self.state == LSPState.CLOSED:
                return
            self.state = LSPState.CLOSED

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

            # Close pipes
            if self.process.stdin:
                self.process.stdin.close()
            if self.process.stdout:
                self.process.stdout.close()
            if self.process.stderr:
                self.process.stderr.close()

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

    def _log_event(self, cmd: str, args: Dict, result: Dict, timing: int, **kwargs) -> None:
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
                    # Check if it matches our warm-up file (if set)
                    # User asked: "publishDiagnostics recibido para el URI warm-up"
                    uri = msg.get("params", {}).get("uri", "")
                    if self._warmup_file and self._warmup_file.as_uri() == uri:
                        with self.lock:
                            if self.state != LSPState.READY:
                                self._transition(LSPState.READY)
                                if self.telemetry:
                                    self.telemetry.incr("lsp_ready_count")
                                    self._log_event(
                                        "lsp.state_change",
                                        {},
                                        {"status": "ready"},
                                        1,
                                        reason="publishDiagnostics",
                                    )
        except Exception:
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

        if event.wait(timeout):
            with self.lock:
                result = self._pending_requests.pop(req_id, None)
                self._request_events.pop(req_id, None)
                return result
        else:
            with self.lock:
                self._pending_requests.pop(req_id, None)
                self._request_events.pop(req_id, None)
            return None  # Timeout

    def _send_rpc(self, msg: Dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            return
        try:
            content = json.dumps(msg).encode("utf-8")
            header = f"Content-Length: {len(content)}\r\n\r\n".encode("ascii")
            self.process.stdin.write(header + content)
            self.process.stdin.flush()
        except OSError:
            pass

    def _read_rpc(self) -> Optional[Dict[str, Any]]:
        if not self.process or not self.process.stdout:
            return None
        try:
            line = self.process.stdout.readline()
            if not line:
                return None

            if line.startswith(b"Content-Length: "):
                length = int(line.strip().split(b": ")[1])
                self.process.stdout.readline()  # \r\n
                content = self.process.stdout.read(length)
                return json.loads(content)
        except Exception:
            pass
        return None
