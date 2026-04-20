"""Daemon client for sending requests to a running DaemonRunner."""
from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from src.infrastructure.daemon.protocol import MAX_REQUEST_SIZE, read_request


class DaemonClient:
    """Unix socket client for DaemonRunner RPC."""

    def __init__(self, socket_path: Path, timeout: float = 5.0) -> None:
        self._socket_path = socket_path
        self._timeout = timeout

    @property
    def socket_path(self) -> Path:
        return self._socket_path

    def is_available(self) -> bool:
        """Check if daemon socket exists."""
        return self._socket_path.exists()

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON request to the daemon and return the response."""
        if not self.is_available():
            return {"status": "error", "message": "Daemon not running"}

        payload = json.dumps(request).encode("utf-8") + b"\n"
        if len(payload) > MAX_REQUEST_SIZE:
            return {"status": "error", "message": "Request too large"}

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(self._timeout)
                sock.connect(str(self._socket_path))
                sock.sendall(payload)

                read_result = read_request(sock, MAX_REQUEST_SIZE)
                if not read_result.raw_data:
                    return {"status": "error", "message": "Empty response from daemon"}

                data = read_result.raw_data.decode("utf-8", errors="replace").strip()
                return json.loads(data)
        except socket.timeout:
            return {"status": "error", "message": f"Daemon request timed out ({self._timeout}s)"}
        except ConnectionRefusedError:
            return {"status": "error", "message": "Daemon refused connection"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Send an LSP method request. Returns response dict or None on error."""
        result = self.send({"method": method, "params": params})
        if result.get("status") == "ok":
            return result.get("data")
        return None

    def health(self) -> dict[str, Any]:
        """Request daemon health check."""
        return self.send({"method": "HEALTH", "params": {}})

    def shutdown(self) -> dict[str, Any]:
        """Request daemon shutdown."""
        return self.send({"method": "SHUTDOWN", "params": {}})
