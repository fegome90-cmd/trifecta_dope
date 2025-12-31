"""
Segment Naming Logic (Pure Domain).

This module contains pure functions for segment ID normalization.
No dependencies on infrastructure (FS, CLI, etc.).

Author: Trifecta Team
Date: 2025-12-31
"""

import re


def normalize_segment_id(raw_name: str) -> str:
    """
    Normalize a segment name to a valid segment ID.

    Rules (applied in order):
    1. Strip leading/trailing whitespace
    2. Convert internal spaces to hyphens
    3. Allow only [a-zA-Z0-9_-], replace others with underscore
    4. Convert to lowercase
    5. If result is empty, return "segment"

    Args:
        raw_name: Raw segment name (typically from Path.name)

    Returns:
        Normalized segment ID

    Examples:
        >>> normalize_segment_id("MyProject")
        'myproject'
        >>> normalize_segment_id("my project")
        'my-project'
        >>> normalize_segment_id("my@project!")
        'my_project_'
        >>> normalize_segment_id("   ")
        'segment'
    """
    # Step 1: Strip whitespace
    normalized = raw_name.strip()

    # Step 2: Convert spaces to hyphens
    normalized = normalized.replace(" ", "-")

    # Step 3: Allow only [a-zA-Z0-9_-], replace others with underscore
    # Use regex to replace any character NOT in the allowed set
    normalized = re.sub(r"[^a-zA-Z0-9_-]", "_", normalized)

    # Step 4: Convert to lowercase
    normalized = normalized.lower()

    # Step 5: Fallback if empty
    if not normalized:
        return "segment"

    return normalized
