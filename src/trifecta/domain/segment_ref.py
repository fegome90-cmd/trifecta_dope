"""
SegmentRef - Single Source of Truth for segment identity.

This module provides the canonical SegmentRef dataclass and resolver.
All platform code MUST use resolve_segment_ref() to get segment identity.

Author: Trifecta Team
Date: 2026-03-06
"""

from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class SegmentRef:
    """
    Unified segment reference with full platform paths.

    This is the SINGLE SOURCE OF TRUTH for segment identity.
    All modules MUST use resolve_segment_ref() to obtain SegmentRef instances.
    """

    repo_root: Path
    repo_id: str
    segment_root: Path
    segment_id: str
    runtime_dir: Path
    registry_key: str
    telemetry_dir: Path
    config_dir: Path
    cache_dir: Path


def _get_platform_data_dir() -> Path:
    """Get platform-appropriate data directory."""
    if trifecta_home := os.environ.get("TRIFECTA_HOME"):
        return Path(trifecta_home).expanduser().resolve()

    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "trifecta"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        base = Path(appdata) / "trifecta"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        base = Path(xdg_data) / "trifecta"

    return base.resolve()


def _canonicalize_path(path: Path | str) -> Path:
    """Canonicalize path using realpath."""
    return Path(path).expanduser().resolve()


def _compute_hash(path: Path, length: int = 8) -> str:
    """Compute SHA256 hash of path string."""
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:length]


def _normalize_segment_id(name: str) -> str:
    """Normalize segment name to valid ID."""
    normalized = name.strip().replace(" ", "-")
    import re

    normalized = re.sub(r"[^a-zA-Z0-9_-]", "_", normalized)
    return normalized.lower() or "segment"


def resolve_segment_ref(
    segment_input: Path | str | None = None,
    hash_length: int = 8,
) -> SegmentRef:
    """
    Resolve segment identity from any input path.

    This is the SINGLE SOURCE OF TRUTH for segment identity.
    All platform code MUST use this function.

    Args:
        segment_input: Path to segment root (default: cwd)
        hash_length: Length of hash to use (default: 8)

    Returns:
        SegmentRef with all identity fields and paths
    """
    if segment_input is None or str(segment_input) == ".":
        input_path = Path.cwd()
    else:
        input_path = Path(segment_input)

    segment_root = _canonicalize_path(input_path)
    segment_name = _normalize_segment_id(segment_root.name)
    segment_hash = _compute_hash(segment_root, hash_length)
    segment_id = f"{segment_name}_{segment_hash}"

    repo_root = _find_repo_root(segment_root)
    repo_id = _compute_hash(repo_root, hash_length)

    platform_data = _get_platform_data_dir()

    runtime_dir = platform_data
    registry_key = segment_id
    telemetry_dir = platform_data / "telemetry" / segment_id
    config_dir = platform_data / "config"
    cache_dir = platform_data / "cache" / segment_id

    return SegmentRef(
        repo_root=repo_root,
        repo_id=repo_id,
        segment_root=segment_root,
        segment_id=segment_id,
        runtime_dir=runtime_dir,
        registry_key=registry_key,
        telemetry_dir=telemetry_dir,
        config_dir=config_dir,
        cache_dir=cache_dir,
    )


def _find_repo_root(start: Path) -> Path:
    """Find repository root by walking up for .git or pyproject.toml."""
    current = start
    while True:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        parent = current.parent
        if parent == current:
            return start
        current = parent


def resolve_segment_ref_deprecated(
    segment_input: Path | str | None = None,
) -> SegmentRef:
    """
    DEPRECATED: Use resolve_segment_ref() instead.

    This function exists for backward compatibility.
    Emits deprecation warning when called.
    """
    import warnings

    warnings.warn(
        "resolve_segment_ref_deprecated() is deprecated. Use resolve_segment_ref() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return resolve_segment_ref(segment_input)
