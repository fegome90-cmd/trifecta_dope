"""Unit tests for CLI introspection module.

Tests runtime introspection of Click commands without relying on
static flag mappings.
"""

import click
import pytest

from src.cli.introspection import (
    OptionSpec,
    introspect_click_params,
    resolve_command_path,
    get_valid_flags_for_command,
    CommandIntrospector,
    IntrospectionError,
)


class TestOptionSpec:
    """Tests for OptionSpec dataclass."""

    def test_basic_creation(self):
        """OptionSpec can be created with required fields."""
        spec = OptionSpec(
            name="verbose",
            opts=("--verbose", "-v"),
            required=False,
            type_name="BOOLEAN",
        )
        assert spec.name == "verbose"
        assert spec.opts == ("--verbose", "-v")
        assert not spec.required
        assert spec.type_name == "BOOLEAN"

    def test_all_names_returns_list(self):
        """all_names() returns all flag variations."""
        spec = OptionSpec(
            name="help",
            opts=("--help", "-h"),
            required=False,
            type_name="BOOLEAN",
        )
        names = spec.all_names()
        assert "--help" in names
        assert "-h" in names

    def test_immutability(self):
        """OptionSpec is frozen (immutable)."""
        spec = OptionSpec(
            name="test",
            opts=("--test",),
            required=False,
            type_name="STRING",
        )
        with pytest.raises(AttributeError):
            spec.name = "modified"

    def test_optional_fields(self):
        """OptionSpec supports optional fields."""
        spec = OptionSpec(
            name="output",
            opts=("--output", "-o"),
            required=True,
            type_name="STRING",
            help="Output file path",
            default="stdout",
            is_flag=False,
            multiple=False,
        )
        assert spec.help == "Output file path"
        assert spec.default == "stdout"
        assert not spec.is_flag
        assert not spec.multiple


class TestIntrospectClickParams:
    """Tests for introspect_click_params function."""

    def test_simple_command(self):
        """Introspect a simple Click command."""

        @click.command()
        @click.option("--verbose", "-v", is_flag=True, help="Enable verbose mode")
        @click.option("--count", "-c", default=1, help="Number of iterations")
        def simple_cmd(verbose, count):
            pass

        specs = introspect_click_params(simple_cmd)

        # Should find 3 options (verbose, count, and --help)
        assert len(specs) == 3

        # Find verbose option
        verbose_spec = next((s for s in specs if s.name == "verbose"), None)
        assert verbose_spec is not None
        assert "--verbose" in verbose_spec.opts
        assert "-v" in verbose_spec.opts
        assert verbose_spec.is_flag
        assert not verbose_spec.required

    def test_command_with_required_option(self):
        """Introspect command with required options."""

        @click.command()
        @click.option("--name", required=True, help="Required name")
        def required_cmd(name):
            pass

        specs = introspect_click_params(required_cmd)

        name_spec = next((s for s in specs if s.name == "name"), None)
        assert name_spec is not None
        assert name_spec.required

    def test_empty_command(self):
        """Introspect command with no options (but --help is always present)."""

        @click.command()
        def empty_cmd():
            pass

        specs = introspect_click_params(empty_cmd)
        # Should find 1 option (--help is always added)
        assert len(specs) == 1
        assert specs[0].name == "help"

    def test_invalid_input_raises_error(self):
        """Passing non-Command raises IntrospectionError."""
        with pytest.raises(IntrospectionError):
            introspect_click_params("not a command")

    def test_boolean_type_detection(self):
        """Boolean types are detected correctly."""

        @click.command()
        @click.option("--flag1", is_flag=True)
        @click.option("--flag2", type=bool)
        def bool_cmd(flag1, flag2):
            pass

        specs = introspect_click_params(bool_cmd)

        for spec in specs:
            assert spec.is_flag or spec.type_name == "BOOLEAN"


class TestResolveCommandPath:
    """Tests for resolve_command_path function."""

    def test_root_command(self):
        """Resolve to root command."""

        @click.group()
        def root():
            pass

        result = resolve_command_path(root, ["trifecta"])
        assert result is root

    def test_nested_subcommand(self):
        """Resolve to nested subcommand."""

        @click.group()
        def root():
            pass

        @root.command()
        def sub():
            pass

        result = resolve_command_path(root, ["trifecta", "sub"])
        assert result is sub

    def test_deeply_nested(self):
        """Resolve deeply nested subcommand."""

        @click.group()
        def root():
            pass

        @root.group()
        def ctx():
            pass

        @ctx.command()
        def sync():
            pass

        result = resolve_command_path(root, ["trifecta", "ctx", "sync"])
        assert result is sync

    def test_unknown_subcommand_returns_none(self):
        """Unknown subcommand returns None."""

        @click.group()
        def root():
            pass

        result = resolve_command_path(root, ["trifecta", "unknown"])
        assert result is None

    def test_stops_at_options(self):
        """Resolution stops when hitting options."""

        @click.group()
        def root():
            pass

        @root.command()
        @click.option("--flag")
        def sub(flag):
            pass

        # Should resolve 'sub', not try to process --flag
        result = resolve_command_path(root, ["trifecta", "sub", "--flag", "value"])
        assert result is sub


class TestGetValidFlagsForCommand:
    """Tests for get_valid_flags_for_command function."""

    def test_extracts_all_flag_names(self):
        """Extract all flag variations."""

        @click.command()
        @click.option("--verbose", "-v", is_flag=True)
        @click.option("--output", "-o")
        def cmd(verbose, output):
            pass

        flags = get_valid_flags_for_command(cmd)

        assert "--verbose" in flags
        assert "-v" in flags
        assert "--output" in flags
        assert "-o" in flags

    def test_fail_closed_on_error(self):
        """Returns empty set on introspection error."""
        flags = get_valid_flags_for_command("not a command")
        assert flags == set()


class TestCommandIntrospector:
    """Tests for CommandIntrospector class."""

    @pytest.fixture
    def sample_cli(self):
        """Create a sample CLI structure."""

        @click.group()
        def trifecta():
            pass

        @trifecta.command()
        @click.option("--task", "-t", required=True)
        def load(task):
            pass

        @trifecta.group()
        def ctx():
            pass

        @ctx.command()
        @click.option("--query", "-q")
        def search(query):
            pass

        return trifecta

    def test_caching(self, sample_cli):
        """Introspector caches results."""
        introspector = CommandIntrospector(sample_cli)

        # First call
        specs1 = introspector.introspect("trifecta load")
        # Second call should use cache
        specs2 = introspector.introspect("trifecta load")

        assert specs1 is specs2  # Same object from cache

    def test_get_flags(self, sample_cli):
        """get_flags returns all flag names."""
        introspector = CommandIntrospector(sample_cli)

        flags = introspector.get_flags("trifecta load")

        assert "--task" in flags
        assert "-t" in flags

    def test_unknown_path_returns_empty(self, sample_cli):
        """Unknown command path returns empty list."""
        introspector = CommandIntrospector(sample_cli)

        specs = introspector.introspect("trifecta unknown")
        assert specs == []

    def test_clear_cache(self, sample_cli):
        """clear_cache empties the cache."""
        introspector = CommandIntrospector(sample_cli)

        # Populate cache
        introspector.introspect("trifecta load")
        assert len(introspector._cache) > 0

        # Clear cache
        introspector.clear_cache()
        assert len(introspector._cache) == 0

    def test_nested_group(self, sample_cli):
        """Can introspect nested group commands."""
        introspector = CommandIntrospector(sample_cli)

        specs = introspector.introspect("trifecta ctx search")

        # Should find 2 options (query and --help)
        assert len(specs) == 2
        query_spec = next((s for s in specs if s.name == "query"), None)
        assert query_spec is not None


class TestIntegrationWithRealTyper:
    """Integration tests with actual Typer commands.

    These tests verify introspection works with the real CLI structure.
    """

    def test_introspect_real_typer_flags(self):
        """Can introspect flags from real Typer app.

        This test imports the actual CLI and verifies introspection works.
        """
        from src.infrastructure.cli import app

        # Create introspector
        introspector = CommandIntrospector(app)

        # Introspect the root app (should at least have --help)
        flags = introspector.get_flags("trifecta")

        # All Click commands have --help
        assert "--help" in flags

    def test_real_cli_has_expected_commands(self):
        """Verify real CLI has expected top-level commands."""
        from src.infrastructure.cli import app

        # Typer app should have registered commands
        if hasattr(app, "commands"):
            commands = list(app.commands.keys())
            # Should have ctx, ast, session, telemetry
            assert "ctx" in commands or hasattr(app, "registered_groups")
