"""Unit tests for invalid_option_handler module."""

import sys
import pytest

from src.cli.invalid_option_handler import (
    extract_invalid_flag,
    find_similar_flags,
    get_valid_flags_for_command,
    handle_invalid_option_error,
    parse_command_path_from_argv,
    render_enhanced_error,
)


class TestFindSimilarFlags:
    """Tests for find_similar_flags function."""

    def test_exact_match(self):
        """Should return exact match with score 1.0."""
        flags = ["--help", "--segment", "--task"]
        result = find_similar_flags("--help", flags)
        assert len(result) > 0
        assert result[0][0] == "--help"
        assert result[0][1] == 1.0

    def test_partial_match(self):
        """Should return partial matches above cutoff."""
        flags = ["--dry-run", "--help", "--task"]
        result = find_similar_flags("--dry", flags, cutoff=0.5)
        assert len(result) > 0
        assert result[0][0] == "--dry-run"
        assert result[0][1] > 0.5

    def test_no_matches_below_cutoff(self):
        """Should return empty list when no matches above cutoff."""
        flags = ["--help", "--task", "--segment"]
        result = find_similar_flags("--xyz", flags, cutoff=0.9)
        assert result == []

    def test_case_insensitive(self):
        """Should match flags case-insensitively."""
        flags = ["--HELP", "--Task"]
        result = find_similar_flags("--help", flags)
        assert len(result) > 0

    def test_returns_top_3(self):
        """Should return at most top 3 matches."""
        flags = ["--help", "--hello", "--helium", "--heavy", "--head"]
        result = find_similar_flags("--hel", flags)
        assert len(result) <= 3


class TestExtractInvalidFlag:
    """Tests for extract_invalid_flag function."""

    def test_extract_from_no_such_option(self):
        """Should extract flag from 'No such option' message."""
        msg = "No such option: --dry-run"
        result = extract_invalid_flag(msg)
        assert result == "--dry-run"

    def test_extract_with_quotes(self):
        """Should extract flag from quoted message."""
        msg = "Error: No such option: '--dry-run'"
        result = extract_invalid_flag(msg)
        assert result == "--dry-run"

    def test_lowercase_message(self):
        """Should extract from lowercase message."""
        msg = "no such option: --max-steps"
        result = extract_invalid_flag(msg)
        assert result == "--max-steps"

    def test_no_match_returns_none(self):
        """Should return None when no flag found."""
        msg = "Some other error message"
        result = extract_invalid_flag(msg)
        assert result is None


class TestParseCommandPathFromArgv:
    """Tests for parse_command_path_from_argv function."""

    def test_simple_command(self):
        """Should parse simple trifecta command."""
        argv = ["trifecta", "load", "--segment", "."]
        result = parse_command_path_from_argv(argv)
        assert result == "trifecta load"

    def test_subcommand(self):
        """Should parse subcommand path."""
        argv = ["trifecta", "ctx", "plan", "--task", "test"]
        result = parse_command_path_from_argv(argv)
        assert result == "trifecta ctx plan"

    def test_empty_argv(self):
        """Should handle empty argv."""
        result = parse_command_path_from_argv([])
        assert result == "trifecta"

    def test_argv_without_trifecta(self):
        """Should handle argv without trifecta in first position."""
        argv = ["python", "-m", "trifecta", "load"]
        result = parse_command_path_from_argv(argv)
        assert result == "trifecta load"


class TestGetValidFlagsForCommand:
    """Tests for get_valid_flags_for_command function."""

    def test_load_command(self):
        """Should return flags for load command."""
        result = get_valid_flags_for_command("trifecta load")
        assert "--help" in result
        assert "--segment" in result
        assert "--task" in result

    def test_ctx_plan_command(self):
        """Should return flags for ctx plan command."""
        result = get_valid_flags_for_command("trifecta ctx plan")
        assert "--help" in result
        assert "--json" in result

    def test_unknown_command_returns_common(self):
        """Should return common flags for unknown commands."""
        result = get_valid_flags_for_command("trifecta unknown")
        assert "--help" in result


class TestRenderEnhancedError:
    """Tests for render_enhanced_error function."""

    def test_renders_error_header(self):
        """Should render error header with invalid flag."""
        result = render_enhanced_error(
            invalid_flag="--dry-run",
            command_path="trifecta load",
            suggested_flags=[],
        )
        assert "❌ Error: No such option: --dry-run" in result

    def test_renders_suggested_flags(self):
        """Should render suggested flags section."""
        result = render_enhanced_error(
            invalid_flag="--dry",
            command_path="trifecta load",
            suggested_flags=[("--dry-run", 0.8)],
        )
        assert "Posiblemente quisiste decir:" in result
        assert "--dry-run" in result

    def test_renders_help_suggestion(self):
        """Should render --help suggestion."""
        result = render_enhanced_error(
            invalid_flag="--invalid",
            command_path="trifecta load",
            suggested_flags=[],
        )
        assert "Para ver opciones disponibles:" in result
        assert "trifecta load --help" in result

    def test_renders_example_for_load(self):
        """Should render example for load command."""
        result = render_enhanced_error(
            invalid_flag="--invalid",
            command_path="trifecta load",
            suggested_flags=[],
        )
        assert "Ejemplo de uso:" in result
        assert "uv run trifecta load --segment" in result

    def test_renders_example_for_ctx_plan(self):
        """Should render example for ctx plan command."""
        result = render_enhanced_error(
            invalid_flag="--invalid",
            command_path="trifecta ctx plan",
            suggested_flags=[],
        )
        assert "Ejemplo de uso:" in result
        assert "trifecta ctx plan" in result


class TestHandleInvalidOptionError:
    """Integration tests for handle_invalid_option_error function."""

    def test_handles_dry_run_error(self):
        """Should handle --dry-run error for trifecta load."""
        sys.argv = ["trifecta", "load", "--segment", ".", "--task", "test", "--dry-run"]
        error_msg = "No such option: --dry-run"

        result = handle_invalid_option_error(error_msg, sys.argv)

        assert "❌ Error: No such option: --dry-run" in result
        assert "trifecta load --help" in result
        assert "Ejemplo de uso:" in result

    def test_handles_max_steps_error(self):
        """Should handle --max-steps error for trifecta ctx plan."""
        sys.argv = [
            "trifecta",
            "ctx",
            "plan",
            "--segment",
            ".",
            "--task",
            "test",
            "--max-steps",
            "5",
        ]
        error_msg = "No such option: --max-steps"

        result = handle_invalid_option_error(error_msg, sys.argv)

        assert "❌ Error: No such option: --max-steps" in result
        assert "trifecta ctx plan --help" in result

    def test_returns_original_if_no_flag_found(self):
        """Should return original message if flag cannot be extracted."""
        sys.argv = ["trifecta", "load"]
        error_msg = "Some other error"

        result = handle_invalid_option_error(error_msg, sys.argv)

        assert result == error_msg

    def test_suggests_help_for_similar_flags(self):
        """Should suggest --help for typos close to help."""
        sys.argv = ["trifecta", "load", "--hepl"]
        error_msg = "No such option: --hepl"

        result = handle_invalid_option_error(error_msg, sys.argv)

        assert "Posiblemente quisiste decir:" in result
        assert "--help" in result
