"""
SSOT Segment Resolver - Single Source of Truth for segment identity.

This module provides a unified way to resolve segment identity from any path.
Dual-ID strategy:
- segment_slug: name-based for humans (e.g., "my-project")
- segment_fingerprint: hash-based for uniqueness (e.g., "a1b2c3d4")
- segment_id: slug + fingerprint for unique human-readable IDs (e.g., "my-project_a1b2c3d4")

Author: Trifecta Team
Date: 2026-02-15
"""

import hashlib
import warnings
from pathlib import Path
from typing import Optional

from src.domain.naming import normalize_segment_id


class SegmentRef:
    """
    Unified segment reference with dual identity.

    Attributes:
        root_abs: Absolute canonical path to segment root
        slug: Human-readable normalized name (for _ctx/ files, logs)
        fingerprint: Hash-based unique identifier (for sockets, caches, locks)
        id: Combined identifier (slug_fingerprint) for unique operations
    """

    __slots__ = ("_root_abs", "_slug", "_fingerprint", "_id")

    def __init__(self, root_abs: Path, slug: str, fingerprint: str, id: str) -> None:
        object.__setattr__(self, "_root_abs", root_abs)
        object.__setattr__(self, "_slug", slug)
        object.__setattr__(self, "_fingerprint", fingerprint)
        object.__setattr__(self, "_id", id)

    @property
    def root_abs(self) -> Path:
        return self._root_abs

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    @property
    def id(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return f"SegmentRef(slug={self.slug}, fingerprint={self.fingerprint}, root={self.root_abs})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SegmentRef):
            return NotImplemented
        return self.root_abs == other.root_abs

    def __hash__(self) -> int:
        return hash(self.root_abs)


def _canonicalize_path(path: Path) -> Path:
    """
    Canonicalize path using realpath to resolve symlinks and normalize.

    Uses realpath() which:
    - Resolves symlinks
    - Makes path absolute
    - Normalizes separators
    - Resolves .. and .
    """
    return Path(path.expanduser().resolve())


def _compute_fingerprint(root_abs: Path, hash_length: int = 8) -> str:
    """
    Compute hash-based fingerprint from canonical path.

    Args:
        root_abs: Canonical absolute path
        hash_length: Length of hash to return (default 8)

    Returns:
        Hex string of SHA256 hash truncated to hash_length
    """
    path_str = str(root_abs)
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:hash_length]


def resolve_segment_ref(
    segment_input: Optional[Path | str] = None,
    hash_length: int = 8,
) -> SegmentRef:
    """
    Resolve segment identity from any input path.

    Args:
        segment_input: Path to segment root (default: cwd). Can be:
            - Path object
            - String (relative or absolute)
            - "." for current directory
            - None (uses cwd)
        hash_length: Length of fingerprint hash (default 8)

    Returns:
        SegmentRef with dual identity (slug + fingerprint + id)

    Example:
        >>> ref = resolve_segment_ref(Path("/Users/dev/my-project"))
        >>> ref.slug
        'my-project'
        >>> ref.fingerprint
        'a1b2c3d4'
        >>> ref.id
        'my-project_a1b2c3d4'
    """
    if segment_input is None or str(segment_input) == ".":
        input_path = Path.cwd()
    else:
        input_path = Path(segment_input)

    root_abs = _canonicalize_path(input_path)
    slug = normalize_segment_id(root_abs.name)
    fingerprint = _compute_fingerprint(root_abs, hash_length)
    id = f"{slug}_{fingerprint}"

    return SegmentRef(root_abs, slug, fingerprint, id)


def get_segment_root(segment_input: Optional[Path | str] = None) -> Path:
    """
    Get canonical segment root path.

    Convenience function - equivalent to resolve_segment_ref().root_abs
    """
    return resolve_segment_ref(segment_input).root_abs


def get_segment_slug(segment_input: Optional[Path | str] = None) -> str:
    """
    Get human-readable segment slug.

    Convenience function - equivalent to resolve_segment_ref().slug
    """
    return resolve_segment_ref(segment_input).slug


def get_segment_fingerprint(segment_input: Optional[Path | str] = None) -> str:
    """
    Get hash-based segment fingerprint.

    Convenience function - equivalent to resolve_segment_ref().fingerprint
    """
    return resolve_segment_ref(segment_input).fingerprint


def get_segment_id(segment_input: Optional[Path | str] = None) -> str:
    """
    Get combined segment ID (slug_fingerprint).

    Convenience function - equivalent to resolve_segment_ref().id
    """
    return resolve_segment_ref(segment_input).id


def compute_segment_id_deprecated(segment_root: Path) -> str:
    """
    DEPRECATED: Use resolve_segment_ref() instead.

    This function computed segment_id using only hash (8 chars).
    It was used by lsp_daemon, telemetry, and hookify_extractor.
    """
    warnings.warn(
        "compute_segment_id() is deprecated. Use resolve_segment_ref() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_segment_fingerprint(segment_root)


def resolve_segment_root_deprecated(start_path: Optional[Path] = None) -> Path:
    """
    DEPRECATED: Use get_segment_root() instead.

    This function resolved segment root by walking up to find .git or pyproject.toml.
    """
    warnings.warn(
        "resolve_segment_root() is deprecated. Use get_segment_root() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if start_path is None:
        path = Path.cwd().resolve()
    else:
        path = start_path.resolve()

    current = path
    while True:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current.resolve()

        parent = current.parent
        if parent == current:
            break
        current = parent

    return Path.cwd().resolve()
