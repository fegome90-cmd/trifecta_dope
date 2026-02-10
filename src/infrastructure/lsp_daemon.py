import os
import sys
import socket
import time
import json
import signal
import fcntl
import subprocess
from pathlib import Path
from typing import Any, Optional, Dict
from src.infrastructure.lsp_client import LSPClient
from src.infrastructure.telemetry import Telemetry
from src.infrastructure.segment_utils import resolve_segment_root, compute_segment_id
from src.infrastructure.daemon_paths import (
    get_daemon_socket_path,
    get_daemon_lock_path,
    get_daemon_pid_path,
)

# --- Constants ---
DEFAULT_TTL = 180


class LSPDaemonServer:
    def __init__(self, segment_root: Path, ttl_sec: int = DEFAULT_TTL):
        self.root = resolve_segment_root(segment_root)
        self.ttl = ttl_sec
        self.last_activity = time.time()
        self.running = False

        # Unified Segment ID / Dir
        self.segment_id = compute_segment_id(self.root)

        # Use short paths from daemon_paths to avoid AF_UNIX limit
        self.socket_path = get_daemon_socket_path(self.segment_id)
        self.lock_path = get_daemon_lock_path(self.segment_id)
        self.pid_path = get_daemon_pid_path(self.segment_id)

        self.telemetry = Telemetry(self.root)
        self.lsp_client = LSPClient(self.root, self.telemetry)

        self._lock_fp: Any = None

    def start(self):
        """Main Daemon Entrypoint"""
        # 1. Acquire Lock
        self._lock_fp = open(self.lock_path, "w")
        try:
            fcntl.lockf(self._lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            sys.stdout.write("Daemon already running.\n")
            return

        # 2. Write PID
        self.pid_path.write_text(str(os.getpid()))

        # 3. Setup Socket
        if self.socket_path.exists():
            self.socket_path.unlink()

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.socket_path))
        server.listen(1)
        server.settimeout(1.0)  # Check TTL every second

        self.running = True

        # 4. Start LSP Client
        self.lsp_client.start()

        # 5. Signal Handling
        signal.signal(signal.SIGTERM, self._shutdown_signal)
        signal.signal(signal.SIGINT, self._shutdown_signal)

        # 6. Event Loop
        while self.running:
            try:
                # Check TTL
                if time.time() - self.last_activity > self.ttl:
                    self.telemetry.event("lsp.daemon_status", {}, {"status": "shutdown_ttl"}, 1)
                    break

                try:
                    conn, _ = server.accept()
                    conn.settimeout(None)  # Disable inherited timeout
                    self._handle_client(conn)
                except socket.timeout:
                    continue  # Loop to check activity/TTL
            except Exception as e:
                self.telemetry.event(
                    "lsp.daemon_status", {}, {"status": "error", "error": str(e)}, 1
                )
                break

        self.cleanup()

    def _handle_client(self, conn: socket.socket):
        self.last_activity = time.time()
        try:
            # Read line-based JSON
            # For simplicity in this lean implementation, read one packet max 64k or use makefile
            f = conn.makefile("r")
            line = f.readline()
            if not line:
                return

            req = json.loads(line)
            resp = self._process_request(req)

            conn.sendall(json.dumps(resp).encode("utf-8") + b"\n")
        except Exception as e:
            err = {"status": "error", "errors": [{"message": str(e)}]}
            try:
                conn.sendall(json.dumps(err).encode("utf-8") + b"\n")
            except Exception:
                pass
        finally:
            conn.close()

    def _process_request(self, req: Dict) -> Dict:
        method = req.get("method")
        params = req.get("params", {})

        if method == "status":
            return {
                "status": "ok",
                "data": {"state": self.lsp_client.state.value, "pid": os.getpid()},
            }

        elif method == "did_open":
            path_str = params.get("path")
            content = params.get("content")
            if path_str and content:
                self.lsp_client.did_open(Path(path_str), content)
            return {"status": "ok"}

        elif method == "request":
            lsp_method = params.get("method")
            lsp_params = params.get("params")
            start_ns = time.perf_counter_ns()
            result = self.lsp_client.request(lsp_method, lsp_params)
            duration_ms = (time.perf_counter_ns() - start_ns) // 1_000_000

            # Telemetry for requests
            if self.telemetry:
                x_fields = {
                    "method": lsp_method,
                    "resolved": bool(result),
                }
                # Extract target logic if hover/def
                if result and "contents" in result:
                    x_fields["target_file"] = "resolved_content"  # simplified

                self.telemetry.event(
                    "lsp.request",
                    {"method": lsp_method},
                    {"status": "ok" if result else "empty"},
                    max(1, duration_ms),
                    **x_fields,
                )

            if result:
                return {"status": "ok", "data": result}
            else:
                return {"status": "error", "message": "LSP Timeout or Not Ready"}

        return {"status": "error", "message": "Unknown method"}

    def _shutdown_signal(self, signum, frame):
        self.running = False

    def cleanup(self):
        """Clean up daemon resources on shutdown."""
        self.lsp_client.stop()
        if self.socket_path.exists():
            self.socket_path.unlink()
        if self.pid_path.exists():
            self.pid_path.unlink()
        if self._lock_fp:
            fcntl.lockf(self._lock_fp, fcntl.LOCK_UN)
            self._lock_fp.close()
            if self.lock_path.exists():
                self.lock_path.unlink()


class LSPDaemonClient:
    def __init__(self, root: Path):
        self.root = resolve_segment_root(root)
        self.segment_id = compute_segment_id(self.root)

        # Use short paths from daemon_paths
        self.socket_path = get_daemon_socket_path(self.segment_id)
        self.lock_path = get_daemon_lock_path(self.segment_id)
        self.pid_path = get_daemon_pid_path(self.segment_id)

    def connect_or_spawn(self) -> bool:
        """Returns True if connected/spawned, False if error."""
        if self._try_connect():
            return True

        return self._spawn_daemon()

    def _try_connect(self) -> bool:
        if not self.socket_path.exists():
            return False
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(str(self.socket_path))
            s.close()
            return True
        except Exception:
            return False

    def _spawn_daemon(self) -> bool:
        try:
            # We must use sys.executable to ensure we use the same venv
            cmd = [
                sys.executable,
                "-m",
                "src.infrastructure.lsp_daemon",
                "start",
                "--root",
                str(self.root),
            ]
            subprocess.Popen(
                cmd,
                cwd=str(self.root),
                start_new_session=True,  # Detach
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # We don't wait. We just return. Future cmds will connect.
            return True
        except Exception:
            return False

    def send(self, req: Dict) -> Dict:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(str(self.socket_path))
            s.sendall(json.dumps(req).encode("utf-8") + b"\n")
            f = s.makefile("r")
            line = f.readline()
            if line:
                return json.loads(line)  # type: ignore[no-any-return]
        except Exception:
            return {"status": "error", "message": "Connection Failed"}
        finally:
            s.close()
        return {"status": "error", "message": "Empty response"}

    def is_ready(self) -> bool:
        resp = self.send({"method": "status"})
        return resp.get("data", {}).get("state") == "READY"  # type: ignore[no-any-return]

    def request(self, method: str, params: Dict) -> Optional[Dict]:
        resp = self.send({"method": "request", "params": {"method": method, "params": params}})
        if resp.get("status") == "ok":
            return resp.get("data")
        return None


# Define DEFAULT_TTL before its usage in the argument parser
DEFAULT_TTL = 300  # Default TTL in seconds

# Entrypoint
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start"])
    parser.add_argument("--root", required=True)
    parser.add_argument(
        "--ttl", type=int, default=int(os.environ.get("LSP_DAEMON_TTL_SEC", DEFAULT_TTL))
    )
    args = parser.parse_args()

    if args.command == "start":
        server = LSPDaemonServer(Path(args.root), ttl_sec=args.ttl)
        server.start()
