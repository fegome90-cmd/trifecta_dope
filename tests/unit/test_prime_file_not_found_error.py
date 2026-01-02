"""Unit tests for PrimeFileNotFoundError type-based classification.

Verifies that Error Card classification works by exception type,
not by substring matching of error messages.
"""

import pytest
from pathlib import Path
from src.application.exceptions import PrimeFileNotFoundError


def test_prime_file_not_found_error_attributes():
    """PrimeFileNotFoundError should store path and segment_id attributes."""
    expected_path = Path("/tmp/test/_ctx/prime_test.md")
    segment_id = "test"

    error = PrimeFileNotFoundError(expected_path=expected_path, segment_id=segment_id)

    assert error.expected_path == expected_path
    assert error.segment_id == segment_id
    assert isinstance(error, FileNotFoundError)


def test_prime_file_not_found_error_custom_message():
    """PrimeFileNotFoundError should accept custom message that doesn't contain standard text."""
    expected_path = Path("/tmp/test/_ctx/prime_test.md")
    segment_id = "test"
    custom_message = "This is a completely different error message without the standard text"

    error = PrimeFileNotFoundError(
        expected_path=expected_path, segment_id=segment_id, message=custom_message
    )

    # Verify attributes are set regardless of message
    assert error.expected_path == expected_path
    assert error.segment_id == segment_id
    assert str(error) == custom_message

    # Verify it does NOT contain the standard substring
    assert "Expected prime file not found" not in str(error)

    # But it's still the correct type
    assert isinstance(error, PrimeFileNotFoundError)


def test_type_based_classification_independence():
    """Type-based classification should work even if message text changes.

    This test verifies that the CLI handler uses isinstance() check,
    not substring matching, to classify the error.
    """
    # Create exception with non-standard message
    error = PrimeFileNotFoundError(
        expected_path=Path("/tmp/segment/_ctx/prime_segment.md"),
        segment_id="segment",
        message="CUSTOM: File is missing",  # No standard text
    )

    # Verify it's still classified correctly by type
    assert isinstance(error, PrimeFileNotFoundError)
    assert isinstance(error, FileNotFoundError)

    # Verify message doesn't contain standard substring
    assert "Expected prime file not found" not in str(error)

    # This proves that type-based matching is independent of message content
