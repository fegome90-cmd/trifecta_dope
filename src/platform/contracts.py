"""Platform contracts for Trifecta V1 runtime.

Defines the contracts for:
- repo_id: stable identifier for repository instances
- segment_id / runtime_key: context-specific identifiers
- Runtime layout: native-first directory structure
"""

from pathlib import Path


#: Default hash length for fingerprint-based identifiers
DEFAULT_FINGERPRINT_LENGTH = 8


def compute_repo_id(canonical_path: Path, hash_length: int = DEFAULT_FINGERPRINT_LENGTH) -> str:
    """Compute stable repo_id from canonical path.

    The repo_id identifies a local canonical instance of a repository.
    It remains stable as long as the canonical path doesn't change.

    Args:
        canonical_path: Absolute canonical path to repo root
        hash_length: Length of hash to use (default 8)

    Returns:
        Hash-based identifier (e.g., "a1b2c3d4")
    """
    import hashlib

    path_str = str(canonical_path.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:hash_length]


def compute_runtime_key(worktree_path: Path | None = None) -> str | None:
    """Compute runtime_key for worktree-specific context.

    The runtime_key identifies a specific worktree or context within a repo.
    If None, the default runtime (non-worktree) is used.

    Args:
        worktree_path: Path to worktree root, or None for default

    Returns:
        Runtime key or None for default runtime
    """
    if worktree_path is None:
        return None

    import hashlib

    path_str = str(worktree_path.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:8]


#: Standard runtime directory layout
RUNTIME_LAYOUT = {
    "global_config": "~/.config/trifecta/",
    "global_state": "~/.local/share/trifecta/",
    "cache": "~/.cache/trifecta/",
}


def get_repo_runtime_dir(repo_id: str) -> Path:
    """Get runtime directory for a specific repo.

    Args:
        repo_id: The repository identifier

    Returns:
        Path to repo's runtime directory
    """
    from pathlib import Path

    state_dir = Path(RUNTIME_LAYOUT["global_state"]).expanduser()
    return state_dir / "repos" / repo_id


def get_repo_subdirs(repo_id: str) -> dict[str, Path]:
    """Get all standard subdirectories for a repo runtime.

    Args:
        repo_id: The repository identifier

    Returns:
        Dict mapping subdir name to Path
    """
    runtime_dir = get_repo_runtime_dir(repo_id)
    return {
        "root": runtime_dir,
        "repo_json": runtime_dir / "repo.json",
        "ast_db": runtime_dir / "ast.db",
        "anchors_db": runtime_dir / "anchors.db",
        "search_db": runtime_dir / "search.db",
        "runtime_db": runtime_dir / "runtime.db",
        "daemon": runtime_dir / "daemon",
        "locks": runtime_dir / "locks",
        "telemetry": runtime_dir / "telemetry",
        "cache": runtime_dir / "cache",
    }
