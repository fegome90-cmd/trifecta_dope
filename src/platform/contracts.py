"""Platform contracts for Trifecta V1 runtime.

Defines the contracts for:
- repo_id: stable identifier for repository instances
- segment_id / runtime_key: context-specific identifiers
- Runtime layout: native-first directory structure
"""

import hashlib
from pathlib import Path


DEFAULT_FINGERPRINT_LENGTH = 8

# Base directories that should contain all runtime data
ALLOWED_BASES = [
    "~/.local/share/trifecta",
    "~/.config/trifecta",
    "~/.cache/trifecta",
]


def _validate_repo_id(repo_id: str) -> None:
    if ".." in repo_id or "/" in repo_id or "\\" in repo_id:
        raise ValueError("Invalid repo_id: contains path traversal characters")


def _validate_path_within_allowedBases(path: Path, base: Path) -> None:
    resolved = path.resolve()
    base_resolved = base.resolve()
    if not str(resolved).startswith(str(base_resolved)):
        raise ValueError(f"Path resolves outside allowed base: {path}")


def compute_repo_id(canonical_path: Path, hash_length: int = DEFAULT_FINGERPRINT_LENGTH) -> str:
    path_str = str(canonical_path.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:hash_length]


def compute_runtime_key(worktree_path: Path | None = None) -> str | None:
    if worktree_path is None:
        return None
    path_str = str(worktree_path.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:8]


RUNTIME_LAYOUT = {
    "global_config": "~/.config/trifecta/",
    "global_state": "~/.local/share/trifecta/",
    "cache": "~/.cache/trifecta/",
}


def get_repo_runtime_dir(repo_id: str) -> Path:
    _validate_repo_id(repo_id)
    state_dir = Path(RUNTIME_LAYOUT["global_state"]).expanduser().resolve()
    _validate_path_within_allowedBases(state_dir, Path("~/.local/share/trifecta").expanduser())
    return state_dir / "repos" / repo_id


def get_repo_subdirs(repo_id: str) -> dict[str, Path]:
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
