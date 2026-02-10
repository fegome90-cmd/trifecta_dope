"""Golden tests for CLI flag introspection.

These tests capture the actual flags from real CLI commands and compare them
against expected snapshots. This ensures that runtime introspection works
correctly and that changes to CLI flags are detected.

If these tests fail, it means the CLI flags have changed and the snapshots
need to be updated (or the change is unintended).
"""

import subprocess
import json
from pathlib import Path

import pytest

from src.cli.introspection import (
    CommandIntrospector,
    create_introspector,
)
from src.cli.invalid_option_handler import (
    get_valid_flags_for_command,
    reset_introspector,
)


# Snapshot directory
SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "cli_flags"


@pytest.fixture(autouse=True)
def reset_introspector_state():
    """Reset introspector state before each test."""
    reset_introspector()
    yield
    reset_introspector()


def load_snapshot(command_path: str) -> dict:
    """Load a snapshot for a given command path."""
    snapshot_file = SNAPSHOT_DIR / f"{command_path.replace(' ', '_')}.json"
    if not snapshot_file.exists():
        return None
    with open(snapshot_file) as f:
        return json.load(f)


def save_snapshot(command_path: str, data: dict) -> None:
    """Save a snapshot for a given command path."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_file = SNAPSHOT_DIR / f"{command_path.replace(' ', '_')}.json"
    with open(snapshot_file, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


class TestGoldenFlagSnapshots:
    """Golden tests for CLI flag introspection."""

    @pytest.mark.parametrize(
        "command_path",
        [
            "trifecta",
            "trifecta load",
            "trifecta ctx",
            "trifecta ctx plan",
            "trifecta ctx build",
            "trifecta ctx sync",
            "trifecta ctx search",
            "trifecta ctx get",
            "trifecta ctx create",
        ],
    )
    def test_flags_match_snapshot(self, command_path):
        """Test that introspected flags match the snapshot."""
        # Get actual flags from runtime introspection
        actual_flags = get_valid_flags_for_command(command_path)
        actual_flags.sort()

        # Load snapshot
        snapshot = load_snapshot(command_path)

        # If snapshot doesn't exist, create it (for first run)
        if snapshot is None:
            save_snapshot(command_path, {"flags": actual_flags})
            pytest.skip(f"Created snapshot for {command_path}")

        # Compare flags
        expected_flags = snapshot.get("flags", [])
        expected_flags.sort()

        assert actual_flags == expected_flags, (
            f"Flags for {command_path} have changed.\n"
            f"Expected: {expected_flags}\n"
            f"Actual: {actual_flags}\n"
            f"If this change is intentional, update the snapshot."
        )

    def test_trifecta_load_has_expected_flags(self):
        """Test that trifecta load has the expected flags."""
        flags = get_valid_flags_for_command("trifecta load")

        # These are the expected flags for trifecta load
        expected_flags = [
            "--help",
            "--segment",
            "--task",
            "--mode",
            "--telemetry",
        ]

        # Check that all expected flags are present
        for flag in expected_flags:
            assert flag in flags, f"Expected flag {flag} not found in trifecta load"

    def test_trifecta_ctx_plan_has_expected_flags(self):
        """Test that trifecta ctx plan has the expected flags."""
        flags = get_valid_flags_for_command("trifecta ctx plan")

        # These are the expected flags for trifecta ctx plan
        expected_flags = [
            "--help",
            "--segment",
            "--task",
            "--json",
            "--telemetry",
        ]

        # Check that all expected flags are present
        for flag in expected_flags:
            assert flag in flags, f"Expected flag {flag} not found in trifecta ctx plan"


class TestRegressionNoDummyFlags:
    """Regression tests to ensure dummy flags are not suggested."""

    def test_dummy_flag_not_suggested(self):
        """Test that a dummy flag is not suggested as a valid flag."""
        # Get valid flags for a command
        flags = get_valid_flags_for_command("trifecta load")

        # These are flags that should NOT exist
        dummy_flags = [
            "--dummy-flag",
            "--fake-option",
            "--nonexistent",
            "--test-flag-12345",
        ]

        # Check that none of the dummy flags are in the valid flags
        for dummy_flag in dummy_flags:
            assert dummy_flag not in flags, (
                f"Dummy flag {dummy_flag} should not be in valid flags. "
                "This suggests a regression in introspection."
            )

    def test_suggestions_subset_of_valid_flags(self):
        """Test that suggestions are always a subset of valid flags."""
        from src.cli.invalid_option_handler import find_similar_flags

        # Get valid flags for a command
        valid_flags = get_valid_flags_for_command("trifecta load")

        # Test with a typo
        invalid_flag = "--segmet"  # typo of --segment
        suggestions = find_similar_flags(invalid_flag, valid_flags)

        # Extract just the flag names from suggestions
        suggested_flag_names = [flag for flag, _ in suggestions]

        # Verify that all suggestions are in the valid flags
        for suggested_flag in suggested_flag_names:
            assert suggested_flag in valid_flags, (
                f"Suggested flag {suggested_flag} is not in valid flags. "
                "This is a regression - suggestions should always be valid."
            )

    def test_no_hallucinated_flags(self):
        """Test that introspection never hallucinates flags."""
        # Get flags from multiple commands
        commands = [
            "trifecta",
            "trifecta load",
            "trifecta ctx plan",
            "trifecta ctx build",
        ]

        for command_path in commands:
            flags = get_valid_flags_for_command(command_path)

            # All flags should start with -- or - (short form)
            for flag in flags:
                assert flag.startswith("--") or flag.startswith("-"), (
                    f"Flag {flag} for {command_path} does not start with -- or -. "
                    "This suggests a regression in introspection."
                )

            # No empty flags
            assert "" not in flags, (
                f"Empty flag found for {command_path}. "
                "This suggests a regression in introspection."
            )


class TestRegressionFlagChanges:
    """Regression tests to detect unintended flag changes."""

    def test_common_flags_always_present(self):
        """Test that common flags are always present in all commands."""
        common_flags = ["--help"]

        commands = [
            "trifecta",
            "trifecta load",
            "trifecta ctx plan",
            "trifecta ctx build",
        ]

        for command_path in commands:
            flags = get_valid_flags_for_command(command_path)
            for common_flag in common_flags:
                assert common_flag in flags, (
                    f"Common flag {common_flag} not found in {command_path}. "
                    "This suggests a regression in CLI structure."
                )

    def test_no_duplicate_flags(self):
        """Test that there are no duplicate flags in any command."""
        commands = [
            "trifecta",
            "trifecta load",
            "trifecta ctx plan",
            "trifecta ctx build",
        ]

        for command_path in commands:
            flags = get_valid_flags_for_command(command_path)

            # Check for duplicates
            unique_flags = set(flags)
            assert len(flags) == len(unique_flags), (
                f"Duplicate flags found in {command_path}: {flags}. "
                "This suggests a regression in introspection."
            )
