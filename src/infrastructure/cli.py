"""Trifecta CLI - Command Line Interface."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from src.domain.models import TrifectaConfig
from src.domain.constants import validate_profile
from src.application.use_cases import (
    CreateTrifectaUseCase,
    ValidateTrifectaUseCase,
    RefreshPrimeUseCase,
    BuildContextPackUseCase,
    MacroLoadUseCase,
    ValidateContextPackUseCase,
    AutopilotUseCase,
)
from src.application.context_service import ContextService
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter

app = typer.Typer(
    name="trifecta",
    help="Generate and manage Trifecta documentation packs for code segments.",
)

ctx_app = typer.Typer(help="Manage Trifecta Context Packs (ctx.search, ctx.get).")
app.add_typer(ctx_app, name="ctx")

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
            typer.echo("   └── _ctx/")
            typer.echo(f"       ├── prime_{config.segment}.md ({len(docs)} docs)")
            typer.echo("       ├── agent.md")
            typer.echo(f"       └── session_{config.segment}.md")
            typer.echo("\n   Remove --dry-run to create files.")
        else:
            typer.echo(f"✅ Trifecta created at {path}")
            typer.echo("   ├── readme_tf.md")
            typer.echo(f"   ├── skill.md ({pack.skill_line_count} lines)")
            typer.echo("   └── _ctx/")
            typer.echo(f"       ├── prime_{config.segment}.md")
            typer.echo("       ├── agent.md")
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


@app.command()
def load(
    segment: str = typer.Option(..., "--segment", "-s", "--path", "-p", help="Segment name or path"),
    task: str = typer.Option(..., "--task", "-t", help="Task description for context selection"),
    mode: str = typer.Option("pcc", "--mode", "-m", help="Mode: pcc (Plan A) or fullfiles (Plan B)"),
) -> None:
    """Macro command to load relevant context for a specific task.
    
    If context_pack.json exists, it uses Programmatic Context Calling (Plan A).
    Otherwise, it falls back to heuristic file selection (Plan B).
    """
    _, file_system = _get_dependencies()
    use_case = MacroLoadUseCase(file_system)
    
    try:
        target_path = _validate_path(segment, must_exist=True)
        output = use_case.execute(target_path, task, mode=mode)
        typer.echo(output)
    except Exception as e:
        typer.echo(_format_error(e, "Load Error"), err=True)
        raise typer.Exit(1)


@ctx_app.command("build")
def ctx_build(
    segment: str = typer.Option(..., "--segment", "-s", "--path", "-p", help="Segment name or path"),
) -> None:
    """Build a Context Pack (context_pack.json) for a segment."""
    _, file_system = _get_dependencies()
    use_case = BuildContextPackUseCase(file_system)
    
    try:
        target_path = _validate_path(segment, must_exist=True)
        pack = use_case.execute(target_path)
        typer.echo(f"✅ Context Pack built: {target_path}/_ctx/context_pack.json")
        typer.echo(f"   - Chunks: {len(pack.chunks)}")
        typer.echo(f"   - Created: {pack.created_at}")
    except Exception as e:
        typer.echo(_format_error(e, "Context Build Error"), err=True)
        raise typer.Exit(1)


@ctx_app.command("search")
def ctx_search(
    segment: str = typer.Option(..., "--segment", "-s", "--path", "-p", help="Segment name or path"),
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    k: int = typer.Option(5, "--limit", "-k", help="Max results"),
    doc: Optional[str] = typer.Option(None, "--doc", help="Filter by doc type (skill, agent, session, prime)"),
) -> None:
    """Search for relevant chunks in the Context Pack."""
    try:
        target_path = _validate_path(segment, must_exist=True)
        service = ContextService(target_path)
        result = service.search(query, k=k, doc_filter=doc)
        
        if not result.hits:
            typer.echo("🔍 No hits found.")
            return

        typer.echo(f"🔍 Search results for: '{query}'" + (f" (filter: {doc})" if doc else ""))
        for hit in result.hits:
            typer.echo(f"  [{hit.id}] (score: {hit.score:.2f}) {hit.source_path}")
            typer.echo(f"    Preview: {hit.preview}")
            typer.echo("")
    except Exception as e:
        typer.echo(_format_error(e, "Context Search Error"), err=True)
        raise typer.Exit(1)


@ctx_app.command("sync")
def ctx_sync(
    segment: str = typer.Option(..., "--segment", "-s", "--path", "-p", help="Segment name or path"),
) -> None:
    """Run Autopilot refresh cycle based on session.md contract."""
    try:
        target_path = _validate_path(segment, must_exist=True)
        _, file_system = _get_dependencies()
        use_case = AutopilotUseCase(file_system)
        typer.echo("🔄 Running Autopilot sync...")
        result = use_case.execute(target_path)
        
        if result["status"] == "skipped":
            typer.echo(f"⏩ Skipped: {result['reason']}")
        elif result["status"] == "error":
            typer.echo(f"❌ Error: {result['reason']}")
            raise typer.Exit(1)
        else:
            for res in result.get("results", []):
                name = res["step"]
                status = "✅" if res["success"] else "❌"
                typer.echo(f"  {status} {name}")
                if not res["success"]:
                     typer.echo(f"     Error: {res.get('stderr') or res.get('error')}")
            typer.echo("✅ Sync completed.")
    except Exception as e:
        typer.echo(_format_error(e, "Context Sync Error"), err=True)
        raise typer.Exit(1)


@ctx_app.command("get")
def ctx_get(
    segment: str = typer.Option(..., "--segment", "-s", "--path", "-p", help="Segment name or path"),
    ids: str = typer.Option(..., "--ids", help="Comma-separated chunk IDs"),
    mode: str = typer.Option("raw", "--mode", "-m", help="Mode: raw, excerpt, skeleton"),
    budget: Optional[int] = typer.Option(None, "--budget-token-est", "--budget", help="Token budget"),
) -> None:
    """Retrieve specific chunks from the Context Pack."""
    try:
        target_path = _validate_path(segment, must_exist=True)
        service = ContextService(target_path)
        id_list = [i.strip() for i in ids.split(",")]
        
        result = service.get(id_list, mode=mode, budget_token_est=budget)
        
        for chunk in result.chunks:
            typer.echo(f"--- CHUNK: {chunk.id} ---")
            typer.echo(chunk.text)
            typer.echo("")
            
        typer.echo(f"📊 Total tokens (est): {result.total_tokens}")
    except Exception as e:
        typer.echo(_format_error(e, "Context Get Error"), err=True)
        raise typer.Exit(1)


@ctx_app.command("validate")
def ctx_validate(
    segment: str = typer.Option(..., "--segment", "-s", "--path", "-p", help="Segment name or path"),
) -> None:
    """Validate Context Pack integrity."""
    try:
        target_path = _validate_path(segment, must_exist=True)
        _, file_system = _get_dependencies()
        use_case = ValidateContextPackUseCase(file_system)
        result = use_case.execute(target_path)
        
        if result.passed:
            typer.echo("✅ Context Pack is healthy.")
        else:
            typer.echo("❌ Context Pack Validation Failed")
            for err in result.errors:
                typer.echo(f"   - Error: {err}")
        
        for warn in result.warnings:
            typer.echo(f"   ⚠️ Warning: {warn}")
            
        if not result.passed:
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(_format_error(e, "Context Validation Error"), err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
