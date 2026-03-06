"""
Platform Contracts - Validation rules for repo_id and segment_id.

These contracts define the expected format and validation rules.

Author: Trifecta Team
Date: 2026-03-06
"""

import re
from pathlib import Path


# Contract: repo_id must be a valid SHA256 hex string of specified length
REPO_ID_PATTERN = re.compile(r"^[a-f0-9]{8,64}$")


def validate_repo_id(repo_id: str) -> bool:
    """
    Validate that a repo_id follows the contract.

    Contract: repo_id must be a lowercase hex string (SHA256 hash).
    Length: 8-64 characters (typically 8 for truncated, 64 for full).
    """
    return bool(REPO_ID_PATTERN.match(repo_id))


def compute_repo_id(repo_root: Path, hash_length: int = 8) -> str:
    """
    Compute repo_id from canonical repo root path.

    This is the canonical way to compute repo_id - all other
    methods should delegate to this function.
    """
    import hashlib

    path_str = str(repo_root.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:hash_length]


# Contract: segment_id must be lowercase alphanumeric with underscores/hyphens
SEGMENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_segment_id(segment_id: str) -> bool:
    """
    Validate that a segment_id follows the contract.

    Contract: segment_id must:
    - Start with alphanumeric
    - Contain only lowercase letters, digits, underscores, hyphens
    - Be at least 1 character
    """
    if not segment_id or len(segment_id) > 128:
        return False
    return bool(SEGMENT_ID_PATTERN.match(segment_id))


# Contract: runtime_key is used for registry/storage keys
RUNTIME_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_runtime_key(runtime_key: str) -> bool:
    """
    Validate that a runtime_key follows the contract.

    Contract: runtime_key must be alphanumeric with underscores/hyphens.
    Used for: file names, registry keys, socket names.
    """
    if not runtime_key or len(runtime_key) > 256:
        return False
    return bool(RUNTIME_KEY_PATTERN.match(runtime_key))
