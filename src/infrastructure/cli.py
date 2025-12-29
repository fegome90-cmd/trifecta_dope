"""Trifecta CLI - Command Line Interface."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from src.domain.models import TrifectaConfig
from src.domain.constants import MAX_SKILL_LINES, validate_profile
from src.application.use_cases import (
    CreateTrifectaUseCase,
    ValidateTrifectaUseCase,
    RefreshPrimeUseCase,
)
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter

app = typer.Typer(
    name="trifecta",
    help="Generate and manage Trifecta documentation packs for code segments.",
)

# Resolve repo root (parent of trifecta_dope)
REPO_ROOT = Path(__file__).parent.parent.parent.parent.resolve()


# ============================================================================
# Custom Exceptions
# ============================================================================

class TrifectaError(Exception):
    """Base exception for Trifecta operations."""
    pass


class ProfileValidationError(TrifectaError):
    """Raised when profile validation fails."""
    pass


class PathValidationError(TrifectaError):
    """Raised when path validation fails."""
    pass


class DocumentationGenerationError(TrifectaError):
    """Raised when documentation generation fails."""
    pass


# ============================================================================
# Error Helper Functions
# ============================================================================

def _format_error(error: Exception, context: str) -> str:
    """Format error with helpful context."""
    return f"❌ {context}\n   Detail: {str(error)}\n   Tip: {_get_tip(error)}"


def _get_tip(error: Exception) -> str:
    """Provide helpful tips based on error type."""
    tips = {
        ValueError: "Check that all required parameters are valid",
        FileNotFoundError: "Verify the path exists and you have access",
        PermissionError: "Check write permissions for the target directory",
        ProfileValidationError: "Use a valid profile from the allowed list",
        PathValidationError: "Ensure the path exists and is accessible",
    }
    return tips.get(type(error), "Run with --help for usage information")


def _validate_path(path_str: str, must_exist: bool = False, must_be_writable: bool = False) -> Path:
    """
    Validate a path for Trifecta operations.

    Args:
        path_str: Path string to validate
        must_exist: Whether the path must already exist
        must_be_writable: Whether the path must be writable

    Returns:
        Resolved Path object

    Raises:
        PathValidationError: If validation fails
    """
    path = Path(path_str).resolve()

    if must_exist and not path.exists():
        raise PathValidationError(
            f"Path does not exist: {path}\n"
            f"  Create it first or use a different path."
        )

    if must_be_writable:
        if path.exists() and not os.access(path, os.W_OK):
            raise PathValidationError(
                f"Path is not writable: {path}\n"
                f"  Check permissions."
            )
        # Check parent directory if path doesn't exist
        if not path.exists():
            parent = path.parent
            if not parent.exists() or not os.access(parent, os.W_OK):
                raise PathValidationError(
                    f"Cannot create path (parent not writable): {path}\n"
                    f"  Parent: {parent}"
                )

    return path


def _get_dependencies() -> tuple[TemplateRenderer, FileSystemAdapter]:
    """Simple dependency injection."""
    return TemplateRenderer(), FileSystemAdapter()


@app.command()
def create(
    segment: str = typer.Option(..., "--segment", "-s", help="Segment name"),
    path: str = typer.Option(..., "--path", "-p", help="Target path"),
    scope: str = typer.Option("", "--scope", help="Scope description"),
    scan_docs: Optional[str] = typer.Option(None, "--scan-docs", help="Docs dir to scan"),
    profile: str = typer.Option("impl_patch", "--profile", help="Default profile"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files"),
) -> None:
    """Create a new Trifecta pack for a segment.

    EXAMPLES:
      # Create a basic Trifecta for debug-terminal segment
      trifecta create --segment debug-terminal --path ./debug_terminal

      # Create with documentation scanning
      trifecta create --segment eval-harness --path ./eval --scan-docs ./docs

      # Create with custom scope and profile
      trifecta create --segment api-client --path ./api_client \\
        --scope "HTTP client for external API" --profile plan

      # Preview without creating files
      trifecta create --segment test --path ./test --dry-run

    TIP: Run `trifecta validate --path ./your-segment` after creation to verify.
    """
    template_renderer, file_system = _get_dependencies()
    use_case = CreateTrifectaUseCase(template_renderer, file_system)

    # Validate profile
    validated_profile = validate_profile(profile)

    # Validate path is writable
    try:
        target_path = _validate_path(path, must_be_writable=True)
    except PathValidationError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    # If scan_docs provided, validate it exists
    scan_path = None
    if scan_docs:
        try:
            scan_path = _validate_path(scan_docs, must_exist=True)
        except PathValidationError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1)

    config = TrifectaConfig(
        segment=segment,
        scope=scope or f"Segment {segment}",
        repo_root=str(REPO_ROOT),
        default_profile=validated_profile,
        last_verified=datetime.now().strftime("%Y-%m-%d"),
    )

    # Scan docs if requested
    docs: list[str] = []
    if scan_path:
        docs = file_system.scan_docs(scan_path, REPO_ROOT)

    try:
        pack = use_case.execute(config, target_path, docs, dry_run=dry_run)

        if dry_run:
            typer.echo(f"🔍 DRY RUN - Preview for {path}")
            typer.echo(f"   ── Files would be created:")
            typer.echo(f"   ├── readme_tf.md ({len(pack.readme_content)} chars)")
            typer.echo(f"   ├── skill.md ({pack.skill_line_count} lines)")
            typer.echo(f"   └── _ctx/")
            typer.echo(f"       ├── prime_{config.segment}.md ({len(docs)} docs)")
            typer.echo(f"       ├── agent.md")
            typer.echo(f"       └── session_{config.segment}.md")
            typer.echo(f"\n   Remove --dry-run to create files.")
        else:
            typer.echo(f"✅ Trifecta created at {path}")
            typer.echo(f"   ├── readme_tf.md")
            typer.echo(f"   ├── skill.md ({pack.skill_line_count} lines)")
            typer.echo(f"   └── _ctx/")
            typer.echo(f"       ├── prime_{config.segment}.md")
            typer.echo(f"       ├── agent.md")
            typer.echo(f"       └── session_{config.segment}.md")
    except ValueError as e:
        typer.echo(_format_error(e, "Validation Error"), err=True)
        raise typer.Exit(1)
    except (FileNotFoundError, PermissionError) as e:
        typer.echo(_format_error(e, "Path Error"), err=True)
        raise typer.Exit(1)
    except TrifectaError as e:
        typer.echo(_format_error(e, "Trifecta Error"), err=True)
        raise typer.Exit(1)


@app.command()
def validate(
    path: str = typer.Option(..., "--path", "-p", help="Path to Trifecta"),
) -> None:
    """Validate an existing Trifecta pack.

    EXAMPLES:
      # Validate a Trifecta pack
      trifecta validate --path ./debug_terminal

      # Validate using short option
      trifecta validate -p ./eval

    Checks:
      ✓ skill.md exists and is within line limit
      ✓ readme_tf.md exists
      ✓ _ctx/ directory exists with required files
      ✓ Segment name matches directory structure

    TIP: Run this after creating or modifying a Trifecta pack.
    """
    _, file_system = _get_dependencies()
    use_case = ValidateTrifectaUseCase(file_system)

    # Validate path exists
    try:
        target_path = _validate_path(path, must_exist=True)
    except PathValidationError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    try:
        result = use_case.execute(target_path)

        if result.passed:
            typer.echo(f"✅ Validation PASSED: {path}")
            if result.warnings:
                for w in result.warnings:
                    typer.echo(f"   ⚠️ {w}")
        else:
            typer.echo("❌ Validation FAILED:")
            for e in result.errors:
                typer.echo(f"   - {e}")
            raise typer.Exit(1)
    except (FileNotFoundError, PermissionError) as e:
        typer.echo(_format_error(e, "Path Error"), err=True)
        raise typer.Exit(1)


@app.command()
def refresh_prime(
    path: str = typer.Option(..., "--path", "-p", help="Path to Trifecta"),
    scan_docs: str = typer.Option(..., "--scan-docs", help="Docs dir to scan"),
) -> None:
    """Refresh the prime_*.md file by re-scanning docs.

    EXAMPLES:
      # Refresh prime with new documentation
      trifecta refresh-prime --path ./debug_terminal --scan-docs ./docs

      # Scan from a different docs directory
      trifecta refresh-prime -p ./eval -s ./documentation

    Use this when:
      • New documentation has been added
      • Documentation structure has changed
      • You want to update the reading list for agents

    TIP: The prime file is located at _ctx/prime_{segment}.md
    """
    template_renderer, file_system = _get_dependencies()
    use_case = RefreshPrimeUseCase(template_renderer, file_system)

    # Validate paths
    try:
        target_path = _validate_path(path, must_exist=True)
        scan_path = _validate_path(scan_docs, must_exist=True)
    except PathValidationError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    try:
        prime_name = use_case.execute(target_path, scan_path, REPO_ROOT)
        docs = file_system.scan_docs(scan_path, REPO_ROOT)
        typer.echo(f"✅ Refreshed {prime_name} with {len(docs)} docs")
    except FileNotFoundError as e:
        typer.echo(_format_error(e, "File Not Found"), err=True)
        raise typer.Exit(1)
    except (PermissionError, PathValidationError) as e:
        typer.echo(_format_error(e, "Path Error"), err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
