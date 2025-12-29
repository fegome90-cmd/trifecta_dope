import os
import fcntl
import tempfile
from pathlib import Path
from contextlib import contextmanager


class AtomicWriter:
    """Handles atomic writes to ensure file integrity."""
    
    @staticmethod
    def write(target: Path, content: str):
        """Write content to a temporary file then rename it atomically."""
        target_dir = target.parent
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            
        # Create temp file in the same directory to ensure same filesystem (for rename)
        fd, temp_path = tempfile.mkstemp(dir=target_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename
            os.rename(temp_path, target)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e


@contextmanager
def file_lock(lock_path: Path):
    """Simple file-based advisory lock."""
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except BlockingIOError:
        raise RuntimeError(f"Could not acquire lock on {lock_path}. Another process might be writing.")
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
