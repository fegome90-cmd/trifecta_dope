import os
import socket
from pathlib import Path

import pytest

from src.infrastructure.daemon.socket_manager import (
    cleanup_runtime_artifacts,
    close_server,
    create_server,
)


class FakeServer:
    def __init__(self, socket_path: Path) -> None:
        self.socket_path = socket_path
        self.closed = False
        self.timeout: float | None = None

    def bind(self, _: str) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self.socket_path.write_text("")

    def listen(self, _: int) -> None:
        return None

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def close(self) -> None:
        self.closed = True


def test_cleanup_runtime_artifacts_is_idempotent(tmp_path: Path) -> None:
    socket_path = tmp_path / "daemon" / "socket"
    pid_path = tmp_path / "daemon" / "pid"
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.write_text("")
    pid_path.write_text("123")

    cleanup_runtime_artifacts(socket_path, pid_path)
    cleanup_runtime_artifacts(socket_path, pid_path)

    assert socket_path.exists() is False
    assert pid_path.exists() is False


def test_close_server_accepts_none() -> None:
    close_server(None)


def test_create_server_writes_pid_and_sets_timeout(monkeypatch, tmp_path: Path) -> None:
    socket_path = tmp_path / "daemon" / "socket"
    pid_path = tmp_path / "daemon" / "pid"
    fake_server = FakeServer(socket_path)

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: fake_server)
    monkeypatch.setattr(os, "chmod", lambda *_args, **_kwargs: None)

    server = create_server(socket_path, pid_path)

    assert server is fake_server
    assert fake_server.timeout == 1.0
    assert pid_path.read_text() == str(os.getpid())


def test_create_server_cleans_artifacts_on_failure(monkeypatch, tmp_path: Path) -> None:
    socket_path = tmp_path / "daemon" / "socket"
    pid_path = tmp_path / "daemon" / "pid"
    fake_server = FakeServer(socket_path)

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: fake_server)
    monkeypatch.setattr(
        os,
        "chmod",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("chmod failed")),
    )

    with pytest.raises(OSError, match="chmod failed"):
        create_server(socket_path, pid_path)

    assert fake_server.closed is True
    assert socket_path.exists() is False
    assert pid_path.exists() is False
