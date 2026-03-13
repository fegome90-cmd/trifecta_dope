import json
import os
import socket
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

import src.infrastructure.cli as cli_module
from src.application.repo_use_case import RepoUseCase
from src.infrastructure.cli import _is_runtime_dir_allowed, app
from src.platform.daemon_manager import ALLOWED_BASES

runner = CliRunner()


class FakeConnection:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.sent: list[bytes] = []
        self.closed = False
        self.timeout: float | None = None

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def recv(self, _: int) -> bytes:
        return self._payload

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True


class FakeServer:
    def __init__(self, socket_path: Path, connections: list[FakeConnection]) -> None:
        self._socket_path = socket_path
        self._connections = list(connections)
        self.closed = False
        self.timeout: float | None = None

    def bind(self, _: str) -> None:
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)
        self._socket_path.write_text("")

    def listen(self, _: int) -> None:
        return None

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def accept(self) -> tuple[FakeConnection, None]:
        if not self._connections:
            raise socket.timeout()
        return self._connections.pop(0), None

    def close(self) -> None:
        self.closed = True



def test_runtime_dir_guard_accepts_descendant_of_allowed_base() -> None:
    base = ALLOWED_BASES[0]
    runtime_dir = base / "repos" / "safe-segment" / "runtime"

    assert _is_runtime_dir_allowed(runtime_dir, ALLOWED_BASES) is True



def test_runtime_dir_guard_rejects_prefixed_sibling_path() -> None:
    base = ALLOWED_BASES[0]
    runtime_dir = Path(str(base) + "-evil/runtime")

    assert runtime_dir.is_relative_to(base) is False
    assert _is_runtime_dir_allowed(runtime_dir, ALLOWED_BASES) is False



def test_daemon_run_rejects_prefixed_sibling_runtime_dir(monkeypatch) -> None:
    base = ALLOWED_BASES[0]
    monkeypatch.setenv("TRIFECTA_RUNTIME_DIR", str(Path(str(base) + "-evil/runtime")))

    result = runner.invoke(app, ["daemon", "run"])

    assert result.exit_code == 1
    output = result.stdout + getattr(result, "stderr", "")
    assert "Invalid runtime directory" in output



def test_daemon_run_cleans_runtime_artifacts_on_socket_setup_failure(
    monkeypatch, tmp_path: Path
) -> None:
    runtime_dir = tmp_path / "runtime"
    socket_path = runtime_dir / "daemon" / "socket"
    pid_path = runtime_dir / "daemon" / "pid"
    fake_server = FakeServer(socket_path=socket_path, connections=[])

    monkeypatch.setenv("TRIFECTA_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setattr(cli_module, "ALLOWED_BASES", [tmp_path])
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: fake_server)
    monkeypatch.setattr(os, "chmod", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("chmod failed")))

    result = runner.invoke(app, ["daemon", "run"])

    assert result.exit_code == 1
    output = result.stdout + getattr(result, "stderr", "")
    assert "Failed to initialize daemon socket" in output
    assert fake_server.closed is True
    assert socket_path.exists() is False
    assert pid_path.exists() is False



def test_daemon_run_returns_error_for_unknown_command(monkeypatch, tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    socket_path = runtime_dir / "daemon" / "socket"
    unknown_conn = FakeConnection(b"WHOAMI")
    shutdown_conn = FakeConnection(b"SHUTDOWN")
    fake_server = FakeServer(socket_path=socket_path, connections=[unknown_conn, shutdown_conn])

    monkeypatch.setenv("TRIFECTA_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setattr(cli_module, "ALLOWED_BASES", [tmp_path])
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: fake_server)

    result = runner.invoke(app, ["daemon", "run"])

    assert result.exit_code == 0
    assert unknown_conn.sent == [b"ERROR: Unknown command\n"]
    assert unknown_conn.closed is True
    assert shutdown_conn.sent == [b"OK\n"]
    assert shutdown_conn.closed is True
    assert fake_server.closed is True



def test_repo_register_alias_json_contract(monkeypatch) -> None:
    entry = SimpleNamespace(
        repo_id="repo-123",
        path="/tmp/example",
        slug="example",
        fingerprint="abcd1234",
    )
    monkeypatch.setattr(RepoUseCase, "register", lambda self, path: entry)

    result = runner.invoke(app, ["repo-register", "/tmp/example", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"repo_id": "repo-123", "path": "/tmp/example"}



def test_repo_list_alias_json_contract(monkeypatch) -> None:
    repos = [
        SimpleNamespace(repo_id="repo-123", path="/tmp/example-1", slug="example-1"),
        SimpleNamespace(repo_id="repo-456", path="/tmp/example-2", slug="example-2"),
    ]
    monkeypatch.setattr(RepoUseCase, "list_repos", lambda self: repos)

    result = runner.invoke(app, ["repo-list", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
        {"repo_id": "repo-123", "path": "/tmp/example-1"},
        {"repo_id": "repo-456", "path": "/tmp/example-2"},
    ]



def test_repo_show_alias_json_contract(monkeypatch) -> None:
    entry = SimpleNamespace(
        repo_id="repo-123",
        path="/tmp/example",
        slug="example",
        fingerprint="abcd1234",
    )
    monkeypatch.setattr(RepoUseCase, "show", lambda self, repo_id: entry)

    result = runner.invoke(app, ["repo-show", "repo-123", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "repo_id": "repo-123",
        "path": "/tmp/example",
        "slug": "example",
    }



def test_command_registration_is_unique() -> None:
    command_names = [command.name for command in app.registered_commands]
    group_names = [group.name for group in app.registered_groups]

    assert command_names.count("status") == 1
    assert command_names.count("doctor") == 1
    assert command_names.count("repo") == 0
    assert group_names.count("repo") == 1
