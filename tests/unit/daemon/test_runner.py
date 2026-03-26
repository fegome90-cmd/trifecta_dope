import json
import socket
from pathlib import Path

import pytest

from src.infrastructure.daemon.runner import DaemonRunner
from src.infrastructure.lsp_client import LSPState


class FakeConnection:
    def __init__(
        self,
        payload: bytes = b"",
        *,
        recv_error: Exception | None = None,
        send_error: Exception | None = None,
    ) -> None:
        self._payload = payload
        self._recv_error = recv_error
        self._send_error = send_error
        self.sent: list[bytes] = []
        self.closed = False
        self.timeout: float | None = None

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def recv(self, size: int) -> bytes:
        if self._recv_error is not None:
            raise self._recv_error
        if not self._payload:
            return b""
        chunk = self._payload[:size]
        self._payload = self._payload[size:]
        return chunk

    def sendall(self, data: bytes) -> None:
        if self._send_error is not None:
            raise self._send_error
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True


class FakeLSPClient:
    def __init__(self, state: LSPState = LSPState.READY) -> None:
        self.state = state
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def is_ready(self) -> bool:
        return self.state == LSPState.READY

    def request(self, method: str, params: dict):
        return {"method": method, "params": params}


def make_runner(tmp_path: Path) -> DaemonRunner:
    return DaemonRunner(runtime_dir=tmp_path, repo_root=tmp_path)


def test_from_env_requires_runtime_dir(monkeypatch) -> None:
    monkeypatch.delenv("TRIFECTA_RUNTIME_DIR", raising=False)

    with pytest.raises(ValueError, match="TRIFECTA_RUNTIME_DIR not set"):
        DaemonRunner.from_env([])


def test_from_env_rejects_invalid_runtime_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TRIFECTA_RUNTIME_DIR", str(tmp_path / "runtime"))

    with pytest.raises(ValueError, match="Invalid runtime directory"):
        DaemonRunner.from_env([])


def test_health_payload_golden(monkeypatch, tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    runner.start_time = 100.0
    runner.lsp_client = FakeLSPClient(LSPState.READY)
    conn = FakeConnection(b"HEALTH\n")

    monkeypatch.setattr("src.infrastructure.daemon.runner.os.getpid", lambda: 4321)
    monkeypatch.setattr("src.infrastructure.daemon.runner.time.time", lambda: 103.0)

    runner._handle_connection(conn)

    assert conn.sent == [
        (
            b'{"status": "ok", "pid": 4321, "uptime": 3, "version": "1.0.0", '
            b'"protocol": ["PING", "HEALTH", "SHUTDOWN"], '
            b'"lsp": {"state": "READY", "enabled": true}}\n'
        )
    ]
    assert conn.closed is True


def test_unknown_command_error_text_frozen(tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    conn = FakeConnection(b"WHOAMI\n")

    runner._handle_connection(conn)

    assert conn.sent == [b"ERROR: Unknown command\n"]


def test_timeout_error_text_frozen(tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    conn = FakeConnection(recv_error=socket.timeout())

    runner._handle_connection(conn)

    assert conn.sent == [b"ERROR: Timeout\n"]


def test_shutdown_command_stops_runner(tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    conn = FakeConnection(b"SHUTDOWN\n")

    runner._handle_connection(conn)

    assert conn.sent == [b"OK\n"]
    assert runner.running is False


def test_json_request_uses_lsp_handler(tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    runner.lsp_client = FakeLSPClient(LSPState.READY)
    conn = FakeConnection(b'{"method":"textDocument/definition","params":{"x":1}}\n')

    runner._handle_connection(conn)

    payload = json.loads(conn.sent[0].decode())
    assert payload == {
        "status": "ok",
        "capability_state": "FULL",
        "backend": "lsp_pyright",
        "response_state": "complete",
        "data": {"method": "textDocument/definition", "params": {"x": 1}},
    }


def test_request_too_large_response_frozen_multi_chunk(tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    oversized = b"x" * 16_385
    conn = FakeConnection(oversized)

    runner._handle_connection(conn)

    assert conn.sent == [b'{"status": "error", "message": "Request too large (max 16KB)"}\n']


def test_send_failure_does_not_raise_from_handle_connection(monkeypatch, tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    conn = FakeConnection(b"WHOAMI\n", send_error=BrokenPipeError("peer closed"))
    stderr_messages: list[str] = []

    monkeypatch.setattr("src.infrastructure.daemon.runner.sys.stderr.write", stderr_messages.append)

    runner._handle_connection(conn)

    assert conn.closed is True
    assert stderr_messages == ["Daemon connection send failed: peer closed\n"]


def test_exact_limit_request_with_eof_is_processed(tmp_path: Path) -> None:
    runner = make_runner(tmp_path)
    conn = FakeConnection(b"x" * 16_384)

    runner._handle_connection(conn)

    assert conn.sent == [b"ERROR: Unknown command\n"]
