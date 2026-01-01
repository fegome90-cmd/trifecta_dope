import os
import sys
import socket
import threading
import time
import json
import signal
import fcntl
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from src.infrastructure.lsp_client import LSPClient, LSPState
from src.infrastructure.telemetry import Telemetry

# --- Constants ---
SOCKET_NAME = "daemon.sock"
LOCK_NAME = "daemon.lock"
PID_NAME = "daemon.pid"
DEFAULT_TTL = 180


class LSPDaemonServer:
    def __init__(self, segment_root: Path, ttl_sec: int = DEFAULT_TTL):
        self.root = segment_root
        self.ttl = ttl_sec
        self.last_activity = time.time()
        self.running = False

        self.lsp_dir = (
            self.root / "_ctx" / "lsp" / "restored_seg"
        )  # Assuming fixed seg for now or need to pass it
        # Actually, for Phase 3 user said: "_ctx/lsp/<segment_id>/"
        # I'll rely on cli passing the right root path which already points to segment?
        # Or cli_ast passes root=. and we construct path.
        # Let's standardize: root is the CWD (project root). segment_id is fixed "restored_seg" for audit context.
        self.lsp_dir.mkdir(parents=True, exist_ok=True)

        self.lock_file = self.lsp_dir / LOCK_NAME
        self.pid_file = self.lsp_dir / PID_NAME
        self.socket_path = self.lsp_dir / SOCKET_NAME

        self.telemetry = Telemetry(self.root)
        self.lsp_client = LSPClient(self.root, self.telemetry)

        self._lock_fp = None

    def start(self):
        """Main Daemon Entrypoint"""
        # 1. Acquire Lock
        self._lock_fp = open(self.lock_file, "w")
        try:
            fcntl.lockf(self._lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print("Daemon already running.")
            return

        # 2. Write PID
        self.pid_file.write_text(str(os.getpid()))

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
            except:
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
            result = self.lsp_client.request(lsp_method, lsp_params)
            if result:
                return {"status": "ok", "data": result}
            else:
                return {"status": "error", "message": "LSP Timeout or Not Ready"}

        return {"status": "error", "message": "Unknown method"}

    def _shutdown_signal(self, signum, frame):
        self.running = False

    def cleanup(self):
        self.lsp_client.stop()
        if self.socket_path.exists():
            self.socket_path.unlink()
        if self.pid_file.exists():
            self.pid_file.unlink()
        if self._lock_fp:
            fcntl.lockf(self._lock_fp, fcntl.LOCK_UN)
            self._lock_fp.close()
            if self.lock_file.exists():
                self.lock_file.unlink()


class LSPDaemonClient:
    def __init__(self, root: Path):
        self.root = root
        self.lsp_dir = self.root / "_ctx" / "lsp" / "restored_seg"
        self.socket_path = self.lsp_dir / SOCKET_NAME

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
        except:
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
                return json.loads(line)
        except Exception:
            return {"status": "error", "message": "Connection Failed"}
        finally:
            s.close()
        return {"status": "error", "message": "Empty response"}

    def is_ready(self) -> bool:
        resp = self.send({"method": "status"})
        return resp.get("data", {}).get("state") == "READY"

    def request(self, method: str, params: Dict) -> Optional[Dict]:
        resp = self.send({"method": "request", "params": {"method": method, "params": params}})
        if resp.get("status") == "ok":
            return resp.get("data")
        return None


# Entrypoint
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start"])
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    if args.command == "start":
        server = LSPDaemonServer(Path(args.root))
        server.start()
