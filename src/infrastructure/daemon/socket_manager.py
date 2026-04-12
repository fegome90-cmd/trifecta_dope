import os
import socket
import stat
from pathlib import Path


def cleanup_runtime_artifacts(socket_path: Path, pid_path: Path) -> None:
    for path in (socket_path, pid_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def close_server(server: object | None) -> None:
    if server is None:
        return
    close_method = getattr(server, "close", None)
    if callable(close_method):
        close_method()


def create_server(socket_path: Path, pid_path: Path) -> socket.socket:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        if socket_path.exists():
            socket_path.unlink()
        server.bind(str(socket_path))
        os.chmod(socket_path, stat.S_IRUSR | stat.S_IWUSR)
        server.listen(1)
        server.settimeout(1.0)
        pid_path.write_text(str(os.getpid()))
    except Exception:
        close_server(server)
        cleanup_runtime_artifacts(socket_path, pid_path)
        raise

    return server
