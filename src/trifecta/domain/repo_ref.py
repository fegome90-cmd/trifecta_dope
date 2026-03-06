"""
RepoRef - Single Source of Truth for repository identity.

Author: Trifecta Team
Date: 2026-03-06
"""

from dataclasses import dataclass
from pathlib import Path

from src.trifecta.domain.segment_ref import resolve_segment_ref


@dataclass(frozen=True)
class RepoRef:
    """
    Unified repository reference.

    Provides repo-level identity separate from segment identity.
    """

    repo_root: Path
    repo_id: str


def resolve_repo_ref(repo_input: Path | str | None = None) -> RepoRef:
    """
    Resolve repository identity from any input path.

    Args:
        repo_input: Path to repo root (default: cwd)

    Returns:
        RepoRef with repo identity
    """
    segment_ref = resolve_segment_ref(repo_input)
    return RepoRef(
        repo_root=segment_ref.repo_root,
        repo_id=segment_ref.repo_id,
    )


def get_repo_id(repo_root: Path, hash_length: int = 8) -> str:
    """
    Get repo_id for a given repo root path.

    Convenience function - delegates to resolve_repo_ref().
    """
    return resolve_repo_ref(repo_root).repo_id
