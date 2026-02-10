"""Introspection module for CLI option discovery.

Provides runtime introspection of Click/Typer commands to extract
valid flags and options. This is the single source of truth for
currently available CLI options.

Invariant: Never suggest flags that don't exist in the actual command.
Fail-closed: If introspection fails, return empty set (no hallucination).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Optional

import click


@dataclass(frozen=True)
class OptionSpec:
    """Specification of a CLI option/flag.

    Immutable dataclass representing a discovered option.
    Used for stable testing and comparison.
    """

    name: str
    opts: tuple[str, ...]  # e.g., ("--verbose", "-v")
    required: bool
    type_name: str
    help: Optional[str] = None
    default: Any = None
    is_flag: bool = False
    multiple: bool = False

    def all_names(self) -> list[str]:
        """Return all flag names (long and short forms)."""
        return list(self.opts)

    def __repr__(self) -> str:
        flags = ", ".join(self.opts)
        return f"OptionSpec({flags})"


class IntrospectionError(Exception):
    """Raised when introspection fails."""

    pass


def introspect_click_params(command: click.Command) -> list[OptionSpec]:
    """Extract OptionSpec list from a Click command.

    Args:
        command: A Click Command object

    Returns:
        List of OptionSpec sorted by declaration order

    Raises:
        IntrospectionError: If command introspection fails
    """
    if not isinstance(command, click.Command):
        raise IntrospectionError(f"Expected click.Command, got {type(command)}")

    specs = []

    # Click stores params in command.params list
    for param in getattr(command, "params", []):
        if isinstance(param, click.Option):
            spec = _extract_option_spec(param)
            if spec:
                specs.append(spec)

    # Add --help explicitly (all Click commands have it)
    # Typer/Click adds this automatically, not in params list
    help_spec = OptionSpec(
        name="help",
        opts=("--help", "-h"),
        required=False,
        type_name="BOOLEAN",
        help="Show this message and exit.",
        is_flag=True,
    )
    specs.append(help_spec)

    return specs


def _extract_option_spec(param: click.Option) -> Optional[OptionSpec]:
    """Convert a Click Option to OptionSpec.

    Args:
        param: Click Option parameter

    Returns:
        OptionSpec or None if extraction fails
    """
    try:
        # Extract flag names (--long, -short)
        opts = tuple(param.opts)
        if not opts:
            return None

        # Get option name (first long form or first form)
        name = param.name or opts[0].lstrip("-")

        # Determine type name
        type_name = _get_type_name(param.type)

        # Check if it's a flag (boolean toggle)
        is_flag = getattr(param, "is_flag", False)

        return OptionSpec(
            name=name,
            opts=opts,
            required=param.required,
            type_name=type_name,
            help=param.help,
            default=param.default,
            is_flag=is_flag,
            multiple=param.multiple,
        )
    except Exception as e:
        # Fail-closed: if we can't parse, skip this option
        return None


def _get_type_name(param_type: Any) -> str:
    """Get a string representation of the parameter type."""
    if isinstance(param_type, click.types.ParamType):
        return param_type.name.upper()
    elif hasattr(param_type, "__name__"):
        return param_type.__name__.upper()
    else:
        return str(param_type).upper()


def resolve_command_path(
    root_command: click.Command, argv: list[str], skip_first: bool = True
) -> Optional[click.Command]:
    """Resolve command path from argv to actual Click command.

    Args:
        root_command: Root Click command (e.g., the typer.Typer() app)
        argv: Command line arguments
        skip_first: If True, skip argv[0] (script name)

    Returns:
        Resolved Click command or None if not found
    """
    if not argv:
        return root_command

    # Find starting index
    start_idx = 1 if skip_first else 0

    # Find 'trifecta' in argv
    for i, arg in enumerate(argv[start_idx:], start=start_idx):
        if "trifecta" in arg.lower():
            start_idx = i + 1
            break

    current = root_command

    # Traverse subcommands
    for arg in argv[start_idx:]:
        if arg.startswith("-"):
            # Hit an option, stop traversing
            break

        if isinstance(current, click.Group):
            # Look for subcommand
            if arg in current.commands:
                current = current.commands[arg]
            else:
                # Unknown subcommand
                return None
        else:
            # Not a group, can't traverse further
            break

    return current


def get_valid_flags_for_command(command: click.Command) -> set[str]:
    """Get all valid flag names for a command.

    Args:
        command: Click Command to introspect

    Returns:
        Set of all valid flag strings (e.g., {"--help", "-h", "--verbose"})

    Note:
        Returns empty set if introspection fails (fail-closed)
    """
    try:
        specs = introspect_click_params(command)
        flags = set()
        for spec in specs:
            flags.update(spec.all_names())
        return flags
    except IntrospectionError:
        # Fail-closed: return empty set
        return set()


def get_common_flags() -> set[str]:
    """Return flags common to most commands.

    These are flags that appear in many commands and are safe to suggest
    even if introspection partially fails.
    """
    return {"--help", "-h"}


class CommandIntrospector:
    """High-level introspector with caching.

    Provides caching layer to avoid repeated introspection
    on hot paths.
    """

    def __init__(self, root_command: click.Command):
        # Convert Typer app to Click command if necessary
        if hasattr(root_command, "registered_groups"):
            from typer.main import get_command

            self._root = get_command(root_command)
        else:
            self._root = root_command
        self._cache: dict[str, list[OptionSpec]] = {}

    def introspect(self, command_path: str) -> list[OptionSpec]:
        """Get OptionSpecs for a command path (with caching).

        Args:
            command_path: Path like "trifecta load" or "trifecta ctx plan"

        Returns:
            List of OptionSpec for that command
        """
        if command_path in self._cache:
            return self._cache[command_path]

        # Parse path and resolve command
        parts = command_path.split()
        if not parts:
            return []

        current = self._root
        for part in parts[1:]:  # Skip root name
            # Handle Typer subcommands by converting to Click
            if hasattr(current, "commands"):
                # Click Group
                if part in current.commands:
                    current = current.commands[part]
                else:
                    return []
            elif hasattr(current, "registered_groups"):
                # Typer app - need to find subcommand in registered_groups
                found = False
                for group in current.registered_groups:
                    if hasattr(group, "typer_instance"):
                        typer_instance = group.typer_instance
                        if hasattr(typer_instance, "registered_callback"):
                            # This is a subcommand
                            if hasattr(typer_instance.registered_callback, "name"):
                                if typer_instance.registered_callback.name == part:
                                    from typer.main import get_command

                                    current = get_command(typer_instance)
                                    found = True
                                    break
                if not found:
                    return []
            else:
                return []

        specs = introspect_click_params(current)
        self._cache[command_path] = specs
        return specs

    def get_flags(self, command_path: str) -> set[str]:
        """Get all flag names for a command path."""
        specs = self.introspect(command_path)
        flags = set()
        for spec in specs:
            flags.update(spec.all_names())
        return flags

    def clear_cache(self) -> None:
        """Clear introspection cache."""
        self._cache.clear()


def create_introspector(typer_app) -> CommandIntrospector:
    """Create an introspector from a Typer app.

    Args:
        typer_app: A typer.Typer application

    Returns:
        Configured CommandIntrospector

    Note:
        Typer wraps Click, so we need to unwrap to get the underlying
        Click Group/Command. We use typer.main.get_command() to get
        the actual Click command structure.
    """
    from typer.main import get_command

    # Convert Typer app to Click command
    # This returns a TyperCommand which is a subclass of click.Command
    click_cmd = get_command(typer_app)

    return CommandIntrospector(click_cmd)
