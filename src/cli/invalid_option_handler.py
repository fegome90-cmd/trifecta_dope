"""Invalid Option Handler for CLI error messages.

Provides fuzzy matching and helpful suggestions when users provide invalid flags.
Uses runtime introspection (not static mappings) to ensure suggestions are
always accurate and up-to-date.

Invariant: Never suggest flags that don't exist in the actual command.
Fail-closed: If introspection fails, returns helpful message without suggestions.
"""

from __future__ import annotations

import difflib
import os
import sys
from dataclasses import dataclass
from typing import Optional

from src.cli.introspection import (
    CommandIntrospector,
    create_introspector,
    get_common_flags,
)

# Singleton introspector instance (initialized lazily)
_introspector: Optional[CommandIntrospector] = None


def _get_introspector() -> CommandIntrospector:
    """Get or create the singleton introspector instance.

    Uses lazy import to avoid circular dependency with cli.py
    """
    global _introspector
    if _introspector is None:
        # Lazy import to avoid circular dependency
        from src.infrastructure.cli import app as typer_app

        _introspector = create_introspector(typer_app)
    return _introspector


def reset_introspector() -> None:
    """Reset the introspector (useful for testing)."""
    global _introspector
    _introspector = None


@dataclass(frozen=True)
class InvalidOptionResult:
    """Result of processing an invalid option error."""

    invalid_flag: str
    suggested_flags: list[tuple[str, float]]  # (flag, similarity_score)
    command_path: str  # e.g., "trifecta load" or "trifecta ctx plan"


def find_similar_flags(
    invalid_flag: str, valid_flags: list[str], cutoff: float = 0.5
) -> list[tuple[str, float]]:
    """
    Find similar flags using fuzzy matching.

    Args:
        invalid_flag: The invalid flag provided by the user
        valid_flags: List of valid flags for the command
        cutoff: Minimum similarity score (0.0-1.0) to include a suggestion

    Returns:
        List of (flag, similarity_score) tuples, sorted by similarity (descending)
    """
    if not valid_flags:
        return []

    # Calculate similarity scores for all valid flags
    matches = []
    for flag in valid_flags:
        # Use SequenceMatcher for fuzzy string matching
        similarity = difflib.SequenceMatcher(None, invalid_flag.lower(), flag.lower()).ratio()
        if similarity >= cutoff:
            matches.append((flag, similarity))

    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)

    # Return top 3 matches
    return matches[:3]


def get_valid_flags_for_command(command_path: str) -> list[str]:
    """
    Get list of valid flags for a given command path using runtime introspection.

    This function introspects the actual Typer/Click commands at runtime
    to get the current list of valid flags. No static mapping needed.

    Args:
        command_path: The command path (e.g., "trifecta load", "trifecta ctx plan")

    Returns:
        List of valid flag names

    Note:
        Uses runtime introspection via CommandIntrospector.
        If introspection fails, returns common flags only (fail-closed).
    """
    try:
        introspector = _get_introspector()
        flags = introspector.get_flags(command_path)

        if not flags:
            # Introspection returned empty set, use common flags only
            return list(get_common_flags())

        return sorted(flags)
    except Exception:
        # Fail-closed: if anything fails, return common flags only
        return list(get_common_flags())


def parse_command_path_from_argv(argv: list[str]) -> str:
    """
    Parse the command path from sys.argv.

    Args:
        argv: Command line arguments (typically sys.argv)

    Returns:
        Command path string (e.g., "trifecta ctx plan")
    """
    if not argv:
        return "trifecta"

    # Skip the script name (e.g., "trifecta" or "python -m trifecta")
    # and reconstruct the command path
    parts = []

    # Find where 'trifecta' appears
    start_idx = 0
    for i, arg in enumerate(argv):
        if "trifecta" in arg.lower():
            start_idx = i
            parts.append("trifecta")
            break

    # Collect subcommands until we hit an option (starts with -)
    for arg in argv[start_idx + 1 :]:
        if arg.startswith("-"):
            break
        parts.append(arg)

    return " ".join(parts) if parts else "trifecta"


def extract_invalid_flag(error_message: str) -> Optional[str]:
    """
    Extract the invalid flag from a Typer error message.

    Args:
        error_message: The error message from Typer/Click

    Returns:
        The invalid flag name, or None if not found
    """
    # Common patterns for invalid option messages
    patterns = [
        "No such option:",
        "no such option:",
        "Error: no such option",
    ]

    for pattern in patterns:
        if pattern in error_message:
            # Extract the flag after the pattern
            parts = error_message.split(pattern)
            if len(parts) > 1:
                flag = parts[-1].strip()
                # Clean up any trailing punctuation or whitespace
                flag = flag.split()[0].strip("\"'")
                return flag

    return None


def render_enhanced_error(
    invalid_flag: str,
    command_path: str,
    suggested_flags: list[tuple[str, float]],
    original_error: Optional[str] = None,
) -> str:
    """
    Render an enhanced error message with suggestions.

    Args:
        invalid_flag: The invalid flag that was provided
        command_path: The command path (e.g., "trifecta load")
        suggested_flags: List of (flag, similarity) tuples
        original_error: The original error message (if available)

    Returns:
        Enhanced error message string
    """
    lines = []

    # Header with error (cross-platform icon)
    error_icon = _get_error_icon()
    lines.append(f"{error_icon} Error: No such option: {invalid_flag}")
    lines.append("")

    # Suggested similar flags
    if suggested_flags:
        lines.append("Posiblemente quisiste decir:")
        for flag, similarity in suggested_flags:
            # Calculate percentage for display
            pct = int(similarity * 100)
            if flag == "--help":
                lines.append(f"  {flag:<15} Show help message ({pct}% match)")
            else:
                lines.append(f"  {flag:<15} ({pct}% match)")
        lines.append("")

    # Suggest --help
    lines.append("Para ver opciones disponibles:")
    lines.append(f"  uv run {command_path} --help")
    lines.append("")

    # Example usage
    lines.append("Ejemplo de uso:")

    # Provide context-appropriate example
    if "ctx plan" in command_path:
        lines.append(f'  uv run {command_path} --segment . --task "Implement feature X"')
    elif "load" in command_path:
        lines.append(f'  uv run {command_path} --segment . --task "Implement feature X"')
    elif "search" in command_path:
        lines.append(f'  uv run {command_path} --segment . --query "search term"')
    elif "get" in command_path:
        lines.append(f'  uv run {command_path} --segment . --ids "chunk1,chunk2"')
    elif "create" in command_path:
        lines.append(f'  uv run {command_path} --segment . --scope "Description"')
    else:
        lines.append(f"  uv run {command_path} --segment . --help")

    return "\n".join(lines)


def handle_invalid_option_error(error_message: str, argv: list[str]) -> str:
    """
    Main entry point for handling invalid option errors.

    Args:
        error_message: The original error message from Typer/Click
        argv: Command line arguments

    Returns:
        Enhanced error message with suggestions
    """
    # Extract the invalid flag
    invalid_flag = extract_invalid_flag(error_message)
    if not invalid_flag:
        # Can't parse the error, return original
        return error_message

    # Parse command path
    command_path = parse_command_path_from_argv(argv)

    # Get valid flags for this command (runtime introspection)
    valid_flags = get_valid_flags_for_command(command_path)

    # Find similar flags
    suggested_flags = find_similar_flags(invalid_flag, valid_flags)

    # Render enhanced error
    enhanced_error = render_enhanced_error(
        invalid_flag=invalid_flag,
        command_path=command_path,
        suggested_flags=suggested_flags,
        original_error=error_message,
    )

    # Emit telemetry event
    _emit_invalid_option_telemetry(
        command_path=command_path,
        invalid_flag=invalid_flag,
        suggested_flags=suggested_flags,
        argv=argv,
    )

    return enhanced_error


# Telemetry support

_telemetry_instance = None


def _get_telemetry():
    """Get or create the telemetry instance (lazy import)."""
    global _telemetry_instance
    if _telemetry_instance is None:
        try:
            from src.infrastructure.telemetry import Telemetry

            _telemetry_instance = Telemetry()
        except Exception:
            # Fail silently if telemetry is not available
            pass
    return _telemetry_instance


def _is_tty() -> bool:
    """Check if running in a TTY."""
    return sys.stdout.isatty()


def _get_platform() -> str:
    """Get platform string for telemetry."""
    return sys.platform


def _emit_invalid_option_telemetry(
    command_path: str,
    invalid_flag: str,
    suggested_flags: list[tuple[str, float]],
    argv: list[str],
) -> None:
    """Emit telemetry event for invalid option error."""
    telemetry = _get_telemetry()
    if telemetry is None:
        return

    # Check if --help was suggested
    help_suggested = any(flag == "--help" for flag, _ in suggested_flags)

    # Increment KPI counter
    telemetry.incr("invalid_option_count")

    # Emit event
    telemetry.event(
        cmd="invalid_option",
        args={
            "command_path": command_path,
            "invalid_flag": invalid_flag,
            "argv_len": len(argv),
        },
        result={
            "suggestions_count": len(suggested_flags),
            "help_suggested": help_suggested,
            "had_match": len(suggested_flags) > 0,
        },
        timing_ms=0,  # Error handling is fast, no timing needed
        platform=_get_platform(),
        is_tty=_is_tty(),
    )


def emit_help_used_telemetry(command_path: str, argv: list[str]) -> None:
    """Emit telemetry event when --help is used."""
    telemetry = _get_telemetry()
    if telemetry is None:
        return

    # Increment KPI counter
    telemetry.incr("help_used_count")

    # Emit event
    telemetry.event(
        cmd="help_used",
        args={
            "command_path": command_path,
            "argv_len": len(argv),
        },
        result={},
        timing_ms=0,
        platform=_get_platform(),
        is_tty=_is_tty(),
    )


def get_telemetry_kpis() -> dict:
    """Get current KPI values from telemetry."""
    telemetry = _get_telemetry()
    if telemetry is None:
        return {
            "invalid_option_count": 0,
            "help_used_count": 0,
        }

    return {
        "invalid_option_count": telemetry.metrics.get("invalid_option_count", 0),
        "help_used_count": telemetry.metrics.get("help_used_count", 0),
    }


def reset_telemetry() -> None:
    """Reset the telemetry instance (useful for testing)."""
    global _telemetry_instance
    _telemetry_instance = None


# Cross-platform support

def _supports_unicode() -> bool:
    """Check if the terminal supports Unicode characters.

    Returns:
        True if Unicode is supported, False otherwise (fallback to ASCII)
    """
    # Check if we're on a TTY
    if not sys.stdout.isatty():
        return False

    # Check platform-specific encoding
    encoding = sys.stdout.encoding or ""
    if "utf" in encoding.lower():
        return True

    # Check environment variables
    if os.environ.get("LANG", "").lower().find("utf") != -1:
        return True

    return False


def _get_error_icon() -> str:
    """Get the appropriate error icon for the terminal.

    Returns:
        Unicode error icon if supported, ASCII fallback otherwise
    """
    if _supports_unicode():
        return "❌"
    return "[ERROR]"
