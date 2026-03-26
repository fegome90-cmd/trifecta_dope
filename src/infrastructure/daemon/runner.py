import os
import signal
import socket
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.infrastructure.daemon.lsp_handler import handle_lsp_request
from src.infrastructure.daemon.protocol import (
    MAX_REQUEST_SIZE,
    build_health_payload,
    build_json_response,
    build_request_too_large_response,
    build_text_response,
    decode_request,
    parse_request,
    read_request,
)
from src.infrastructure.daemon.socket_manager import (
    cleanup_runtime_artifacts,
    close_server,
    create_server,
)
from src.infrastructure.lsp_client import LSPClient
from src.infrastructure.telemetry import Telemetry
from src.platform.daemon_manager import ALLOWED_BASES, is_runtime_dir_allowed


@dataclass
class DaemonRunner:
    runtime_dir: Path
    repo_root: Path
    ttl_seconds: int = 0
    lsp_client: Any = field(default=None, init=False)
    server: socket.socket | None = field(default=None, init=False)
    running: bool = field(default=True, init=False)
    start_time: float = field(default=0.0, init=False)

    @classmethod
    def from_env(cls, allowed_bases: list[Path] | None = None) -> "DaemonRunner":
        runtime_dir_env = os.environ.get("TRIFECTA_RUNTIME_DIR")
        if not runtime_dir_env:
            raise ValueError("TRIFECTA_RUNTIME_DIR not set")

        runtime_dir = Path(runtime_dir_env).resolve()
        bases = ALLOWED_BASES if allowed_bases is None else allowed_bases
        if not is_runtime_dir_allowed(runtime_dir, bases):
            raise ValueError("Invalid runtime directory")

        repo_root_env = os.environ.get("TRIFECTA_REPO_ROOT")
        if not repo_root_env:
            raise ValueError("TRIFECTA_REPO_ROOT not set")
        repo_root = Path(repo_root_env).resolve()
        if not repo_root.exists():
            raise ValueError(f"TRIFECTA_REPO_ROOT does not exist: {repo_root}")

        ttl_env = os.environ.get("TRIFECTA_DAEMON_TTL")
        ttl_seconds = int(ttl_env) if ttl_env else 0
        return cls(runtime_dir=runtime_dir, repo_root=repo_root, ttl_seconds=ttl_seconds)

    @property
    def socket_path(self) -> Path:
        return self.runtime_dir / "daemon" / "socket"

    @property
    def pid_path(self) -> Path:
        return self.runtime_dir / "daemon" / "pid"

    def run(self) -> None:
        try:
            self.server = create_server(self.socket_path, self.pid_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize daemon socket: {exc}") from exc

        self._install_signal_handlers()
        self.start_time = time.time()
        self._initialize_lsp_client()
        self._emit_daemon_status()

        try:
            while self.running:
                if self.ttl_seconds > 0 and (time.time() - self.start_time) > self.ttl_seconds:
                    break

                try:
                    conn, _ = self.server.accept()
                    self._handle_connection(conn)
                except socket.timeout:
                    continue
                except Exception as exc:
                    sys.stderr.write(f"Daemon error: {exc}\n")
                    break
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self.lsp_client:
            try:
                self.lsp_client.stop()
            except Exception:
                pass
        close_server(self.server)
        cleanup_runtime_artifacts(self.socket_path, self.pid_path)

    def _install_signal_handlers(self) -> None:
        def shutdown_signal(signum: int, frame: object | None) -> None:
            del signum, frame
            self.running = False

        signal.signal(signal.SIGTERM, shutdown_signal)
        signal.signal(signal.SIGINT, shutdown_signal)

    def _initialize_lsp_client(self) -> None:
        try:
            self.lsp_client = LSPClient(self.repo_root, telemetry=None)
            self.lsp_client.start()
        except Exception:
            self.lsp_client = None

    def _emit_daemon_status(self) -> None:
        try:
            telem = Telemetry(self.runtime_dir)
            telem.event(
                "daemon_status",
                {},
                {
                    "state": "running",
                    "pid": os.getpid(),
                    "uptime": 0,
                    "lsp_enabled": self.lsp_client is not None,
                },
                1,
            )
            telem.flush()
        except Exception:
            pass

    def _safe_close_connection(self, conn: Any) -> None:
        try:
            conn.close()
        except Exception:
            pass

    def _safe_send_and_close(self, conn: Any, payload: bytes) -> None:
        try:
            conn.sendall(payload)
        except Exception as exc:
            sys.stderr.write(f"Daemon connection send failed: {exc}\n")
        finally:
            self._safe_close_connection(conn)

    def _handle_connection(self, conn: Any) -> None:
        conn.settimeout(5.0)
        try:
            read_result = read_request(conn, MAX_REQUEST_SIZE)
            if not read_result.raw_data:
                self._safe_close_connection(conn)
                return
            if read_result.oversized:
                self._safe_send_and_close(conn, build_request_too_large_response())
                return

            data = decode_request(read_result.raw_data)
        except socket.timeout:
            self._safe_send_and_close(conn, build_text_response("ERROR: Timeout"))
            return
        except Exception as exc:
            self._safe_send_and_close(conn, build_text_response(f"ERROR: {str(exc)}"))
            return

        parsed = parse_request(data)
        if parsed["kind"] == "json":
            response = handle_lsp_request(parsed["payload"], self.lsp_client)
            self._safe_send_and_close(conn, build_json_response(response))
            return

        if parsed["kind"] == "empty":
            self._safe_close_connection(conn)
            return

        command = parsed["command"]
        if command == "PING":
            self._safe_send_and_close(conn, build_text_response("PONG"))
        elif command == "HEALTH":
            lsp_state = self.lsp_client.state.value if self.lsp_client else "unavailable"
            payload = build_health_payload(
                pid=os.getpid(),
                uptime=int(time.time() - self.start_time),
                lsp_state=lsp_state,
                lsp_enabled=self.lsp_client is not None,
            )
            self._safe_send_and_close(conn, build_json_response(payload))
        elif command == "SHUTDOWN":
            self._safe_send_and_close(conn, build_text_response("OK"))
            self.running = False
        else:
            self._safe_send_and_close(conn, build_text_response("ERROR: Unknown command"))
