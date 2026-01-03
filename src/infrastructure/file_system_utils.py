import fcntl
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


class AtomicWriter:
    """Handles atomic writes to ensure file integrity."""

    @staticmethod
    def write(path: Path, content: str) -> None:
        """Atomic write via temp file with forced trailing newline for pre-commit compliance."""
        if not content.endswith("\n"):
            content += "\n"

        # Ensure the target directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        try:
            temp_path.write_text(content)
            temp_path.replace(path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise


@contextmanager
def file_lock(lock_path: Path) -> Generator[None, None, None]:
    """Simple file-based advisory lock."""
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except BlockingIOError:
        raise RuntimeError(
            f"Could not acquire lock on {lock_path}. Another process might be writing."
        )
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
