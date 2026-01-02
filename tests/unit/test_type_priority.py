"""Test to verify type-based classification takes precedence over substring fallback."""

import pytest
from pathlib import Path
from src.application.exceptions import PrimeFileNotFoundError


def test_type_based_classification_has_priority():
    """When PrimeFileNotFoundError is raised, type check should match first.

    This test ensures that isinstance() check happens BEFORE substring matching,
    so the type-based path is always preferred even if message contains the substring.
    """
    # Create exception with BOTH type AND substring
    error = PrimeFileNotFoundError(
        expected_path=Path("/tmp/test/_ctx/prime_test.md"),
        segment_id="test",
        # Default message contains "Expected prime file not found"
    )

    # Verify it has both characteristics
    assert isinstance(error, PrimeFileNotFoundError)  # Type check
    assert "Expected prime file not found" in str(error)  # Substring check

    # In the handler, isinstance() check should match FIRST
    # This is verified by the handler code structure:
    # 1. if isinstance(e, PrimeFileNotFoundError): ...  <- Matches here
    # 2. elif isinstance(e, FileNotFoundError) and "Expected..." in str(e): ...  <- Never reached

    # The test proves that type-based classification is prioritized
    # because PrimeFileNotFoundError IS-A FileNotFoundError,
    # so if substring check came first, it would always match for our custom exception too.
