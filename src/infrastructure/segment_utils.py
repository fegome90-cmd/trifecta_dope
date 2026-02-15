import hashlib
import warnings
from pathlib import Path
from typing import Optional


def resolve_segment_root(start_path: Optional[Path] = None) -> Path:
    """
    Resolve the segment root (repo root) by looking for markers.
    Markers: .git, pyproject.toml
    Fallback: cwd

    DEPRECATED: Use get_segment_root() from src.domain.segment_resolver instead.
    """
    warnings.warn(
        "resolve_segment_root() is deprecated. Use get_segment_root() from src.domain.segment_resolver instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if start_path is None:
        path = Path.cwd().resolve()
    else:
        path = start_path.resolve()

    # Walk up to find markers
    current = path
    while True:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current.resolve()

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    return Path.cwd().resolve()


def compute_segment_id(segment_root: Path) -> str:
    """
    Compute stable 8-char SHA256 hash of the segment root path.

    DEPRECATED: Use get_segment_fingerprint() or resolve_segment_ref() from src.domain.segment_resolver instead.
    """
    warnings.warn(
        "compute_segment_id() is deprecated. Use get_segment_fingerprint() or resolve_segment_ref() from src.domain.segment_resolver instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Enforce resolved path string for consistency
    path_str = str(segment_root.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:8]
