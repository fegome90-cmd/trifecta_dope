"""Trifecta CLI with T8 Telemetry."""

import json
import os
import time
from pathlib import Path
from typing import Literal, Optional, Tuple

import typer

from src.application.search_get_usecases import GetChunkUseCase, SearchUseCase
from src.application.use_cases import (
    BuildContextPackUseCase,
    MacroLoadUseCase,
    RefreshPrimeUseCase,
    ValidateContextPackUseCase,
    ValidateTrifectaUseCase,
)
from src.domain.models import TrifectaConfig
from src.infrastructure.file_system import FileSystemAdapter
from src.infrastructure.telemetry import Telemetry
from src.infrastructure.templates import TemplateRenderer

app = typer.Typer(help="Trifecta Context Loading CLI")
ctx_app = typer.Typer(help="Context Pack management commands")
session_app = typer.Typer(help="Session logging commands")

app.add_typer(ctx_app, name="ctx")
app.add_typer(session_app, name="session")

HELP_SEGMENT = "Target segment path (e.g., 'debug_terminal' or '.')"
HELP_TELEMETRY = "Telemetry level: off, lite (default), full"

HELP_TELEMETRY = "Telemetry level: off, lite (default), full"


def _get_telemetry(segment: str, level: str) -> Telemetry:
    """Initialize telemetry."""
    # Convert segment string to path
    path = Path(segment).resolve()
    # Check env override
    env_level = os.environ.get("TRIFECTA_TELEMETRY_LEVEL", level)
    return Telemetry(path, level=env_level)


def _get_dependencies(
    segment: str, telemetry: Optional[Telemetry] = None
) -> Tuple[TemplateRenderer, FileSystemAdapter, Optional[Telemetry]]:
    # Simplified: just return filesystem and template renderer
    fs = FileSystemAdapter()
    template_renderer = TemplateRenderer()
    return template_renderer, fs, telemetry


def _format_error(e: Exception, title: str = "Error") -> str:
    """Format exceptions for CLI output."""
    return f"❌ {title}\n   Detail: {str(e)}"


# =============================================================================
# T8: Stats Command
# =============================================================================


@ctx_app.command("stats")
def ctx_stats(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
) -> None:
    """[T8] Show telemetry stats for a segment."""
    path = Path(segment).resolve()
    telemetry_dir = path / "_ctx" / "telemetry"

    if not telemetry_dir.exists():
        typer.echo(f"No telemetry found at {telemetry_dir}")
        return

    # Load metrics
    metrics = {}
    metrics_path = telemetry_dir / "metrics.json"
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text())
        except Exception:
            pass

    # Load last run
    last_run = {}
    last_run_path = telemetry_dir / "last_run.json"
    if last_run_path.exists():
        try:
            last_run = json.loads(last_run_path.read_text())
        except Exception:
            pass

    typer.echo(f"📊 Telemetry for {segment}")
    typer.echo(f"Path: {telemetry_dir}\n")

    typer.echo("Counters:")
    for k, v in sorted(metrics.items()):
        typer.echo(f"  {k}: {v}")

    # Alias expansion summary
    alias_expansion_count = metrics.get("ctx_search_alias_expansion_count", 0)
    alias_terms_total = metrics.get("ctx_search_alias_terms_total", 0)
    search_count = metrics.get("ctx_search_count", 0)

    if alias_expansion_count > 0 and search_count > 0:
        avg_terms = alias_terms_total / alias_expansion_count if alias_expansion_count > 0 else 0
        typer.echo("\nAlias Expansion:")
        typer.echo(
            f"  {alias_expansion_count} searches expanded ({alias_expansion_count / search_count * 100:.1f}%), avg {avg_terms:.1f} terms"
        )

    if last_run:
        typer.echo("\nLast Run:")
        typer.echo(f"  Timestamp: {last_run.get('ts', 'unknown')}")
        latencies = last_run.get("latencies", {})
        if latencies:
            typer.echo("  Latencies:")
            for cmd, stats in latencies.items():
                count = stats.get("count", 0)
                # Read new keys (p50_ms, p95_ms, max_ms) with backward compat
                p50 = stats.get("p50_ms", stats.get("p50", 0))
                p95 = stats.get("p95_ms", stats.get("p95", 0))
                max_ms = stats.get("max_ms", stats.get("max", 0))

                if count == 0:
                    typer.echo(f"    {cmd}: no samples")
                else:
                    typer.echo(
                        f"    {cmd}: p50={p50:.3f}ms p95={p95:.3f}ms max={max_ms:.3f}ms (n={count})"
                    )

        warnings = last_run.get("top_warnings", [])
        if warnings:
            typer.echo("\n  Top Warnings:")
            for w in warnings:
                typer.echo(f"    - {w}")


# =============================================================================
# Context Commands
# =============================================================================


@ctx_app.command("build")
def build(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Build a Context Pack (context_pack.json) for a segment."""
    from src.domain.result import Err, Ok
    from src.infrastructure.validators import detect_legacy_context_files, validate_segment_fp

    path = Path(segment).resolve()
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()

    # FP Gate: North Star Strict Validation
    match validate_segment_fp(path):
        case Err(errors):
            typer.echo("❌ Validation Failed (North Star Gate):")
            for err in errors:
                typer.echo(f"   - {err}")
            telemetry.event(
                "ctx.build",
                {"segment": segment},
                {"status": "validation_failed", "errors": len(errors)},
                int((time.time() - start_time) * 1000),
            )
            telemetry.flush()
            raise typer.Exit(code=1)
        case Ok(_):
            # Check for legacy file warnings (non-blocking)
            legacy = detect_legacy_context_files(path)
            if legacy:
                typer.echo("⚠️  Warning: Legacy context files detected:")
                for lf in legacy:
                    typer.echo(f"   - _ctx/{lf} (consider renaming)")

    _, file_system, _ = _get_dependencies(segment, telemetry)
    use_case = BuildContextPackUseCase(file_system, telemetry)

    try:
        output = use_case.execute(path)
        typer.echo(output)
        telemetry.event(
            "ctx.build",
            {"segment": segment},
            {"status": "ok"},
            int((time.time() - start_time) * 1000),
        )
    except Exception as e:
        telemetry.event(
            "ctx.build",
            {"segment": segment},
            {"status": "error", "error": str(e)},
            int((time.time() - start_time) * 1000),
        )
        typer.echo(_format_error(e, "Build Failed"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()


@ctx_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Search for relevant chunks in the Context Pack."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = SearchUseCase(file_system, telemetry)

    try:
        output = use_case.execute(Path(segment), query, limit=limit)
        typer.echo(output)
        telemetry.observe("ctx.search", int((time.time() - start_time) * 1000))
    except Exception as e:
        telemetry.event(
            "ctx.search",
            {"query": query},
            {"status": "error"},
            int((time.time() - start_time) * 1000),
        )
        typer.echo(_format_error(e, "Search Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()


@ctx_app.command("get")
def get(
    ids: str = typer.Option(..., "--ids", "-i", help="Comma-separated Chunk IDs"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    mode: Literal["raw", "excerpt", "skeleton"] = typer.Option(
        "excerpt", "--mode", "-m", help="Output mode: raw, excerpt, summary"
    ),
    budget_token_est: int = typer.Option(1500, "--budget-token-est", "-b", help="Max token budget"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Retrieve full content for specific chunks."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = GetChunkUseCase(file_system, telemetry)

    id_list = [x.strip() for x in ids.split(",") if x.strip()]

    try:
        output = use_case.execute(
            Path(segment), id_list, mode=mode, budget_token_est=budget_token_est
        )
        typer.echo(output)
        telemetry.observe("ctx.get", int((time.time() - start_time) * 1000))
    except Exception as e:
        telemetry.event(
            "ctx.get", {"ids": ids}, {"status": "error"}, int((time.time() - start_time) * 1000)
        )
        typer.echo(_format_error(e, "Get Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()


@ctx_app.command("validate")
def validate(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Validate Context Pack health."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = ValidateContextPackUseCase(file_system, telemetry)

    try:
        result = use_case.execute(Path(segment))
        # Format ValidationResult for display
        if result.passed:
            output = "✅ Validation Passed"
            if result.warnings:
                output += "\n\n⚠️  Warnings:\n" + "\n".join(f"   - {w}" for w in result.warnings)
        else:
            output = "❌ Validation Failed\n\n" + "\n".join(f"   - {e}" for e in result.errors)

        typer.echo(output)
        telemetry.observe("ctx.validate", int((time.time() - start_time) * 1000))

        # Exit with error code if validation failed
        if not result.passed:
            raise typer.Exit(code=1)

    except Exception as e:
        telemetry.event(
            "ctx.validate", {}, {"status": "error"}, int((time.time() - start_time) * 1000)
        )
        typer.echo(_format_error(e, "Validation Error"), err=True)
        if not isinstance(e, typer.Exit):
            raise typer.Exit(1)
        raise e
    finally:
        telemetry.flush()


@ctx_app.command("sync")
def sync(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Macro: Build + Validate."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    try:
        typer.echo("🔄 Running build...")
        build_uc = BuildContextPackUseCase(file_system, telemetry)
        build_uc.execute(Path(segment))

        typer.echo("✅ Build complete. Validating...")
        validate_uc = ValidateContextPackUseCase(file_system, telemetry)
        result = validate_uc.execute(Path(segment))

        # Format ValidationResult for display
        if result.passed:
            output = "✅ Validation Passed"
            if result.warnings:
                output += "\n\n⚠️  Warnings:\n" + "\n".join(f"   - {w}" for w in result.warnings)
        else:
            output = "❌ Validation Failed\n\n" + "\n".join(f"   - {e}" for e in result.errors)

        typer.echo(output)

        telemetry.event(
            "ctx.sync",
            {"segment": segment},
            {"status": "ok"},
            int((time.time() - start_time) * 1000),
        )

        if not result.passed:
            raise typer.Exit(code=1)

    except Exception as e:
        telemetry.event(
            "ctx.sync",
            {"segment": segment},
            {"status": "error"},
            int((time.time() - start_time) * 1000),
        )
        typer.echo(_format_error(e, "Sync Error"), err=True)
        if not isinstance(e, typer.Exit):
            raise typer.Exit(1)
        raise e
    finally:
        telemetry.flush()


@ctx_app.command("reset")
def ctx_reset(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
) -> None:
    """[DESTRUCTIVE] Regenerate ALL context files (templates + pack). Use with caution."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    template_renderer, file_system, _ = _get_dependencies(segment, telemetry)

    try:
        if not force:
            typer.echo(
                "⚠️  WARNING: This will overwrite skill.md, agent.md, session.md, readme_tf.md"
            )
            typer.echo("Press Ctrl+C to cancel, or Enter to continue...")
            input()

        typer.echo("🔄 Regenerating templates...")
        config_path = Path(segment) / "_ctx" / "trifecta_config.json"
        if config_path.exists():
            import json

            config_data = json.loads(config_path.read_text())
            from src.domain.models import TrifectaConfig

            config = TrifectaConfig(**config_data)
        else:
            typer.echo("❌ No trifecta_config.json found. Use 'trifecta create' for new segments.")
            raise typer.Exit(1)

        (Path(segment) / "skill.md").write_text(template_renderer.render_skill(config))
        (Path(segment) / "_ctx" / "agent.md").write_text(template_renderer.render_agent(config))
        (Path(segment) / "_ctx" / f"session_{config.segment}.md").write_text(
            template_renderer.render_session(config)
        )
        (Path(segment) / "readme_tf.md").write_text(template_renderer.render_readme(config))

        typer.echo("✅ Templates regenerated. Running sync...")

        build_uc = BuildContextPackUseCase(file_system, telemetry)
        build_uc.execute(Path(segment))

        validate_uc = ValidateContextPackUseCase(file_system, telemetry)
        output = validate_uc.execute(Path(segment))
        typer.echo(output)

        telemetry.observe("ctx.reset", int((time.time() - start_time) * 1000))

        if not output.passed:
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        typer.echo("\n❌ Reset cancelled")
        raise typer.Exit(0)
    except Exception as e:
        telemetry.event(
            "ctx.reset", {}, {"status": "error"}, int((time.time() - start_time) * 1000)
        )
        typer.echo(_format_error(e, "Reset Error"), err=True)
        if not isinstance(e, typer.Exit):
            raise typer.Exit(1)
        raise e
    finally:
        telemetry.flush()


# =============================================================================
# Generator Commands
# =============================================================================


@app.command("create")
def create(
    segment: str = typer.Option(..., "--segment", "-s", help="Segment name (slug)"),
    scope: str = typer.Option("Scope", "--scope", help="Short description of segment scope"),
    path: Path = typer.Option(Path.cwd(), "--path", "-p", help="Target directory (default: CWD)"),
) -> None:
    """
    Scaffold a new Trifecta Segment.

    Generates:
    - skill.md (Rules & Roles)
    - _ctx/prime_{segment}.md (Reading list)
    - _ctx/agent.md (Tech stack)
    - _ctx/session_{segment}.md (Runbook)
    - readme_tf.md (Documentation)
    """
    template_renderer, file_system, _ = _get_dependencies(segment)

    # Dependencies not needed for scaffold mostly
    # But logic is inside a usecase? No, currently scaffold logic was simple enough to be here or moved?
    # Logic in previous version was likely here or implied.
    # Let's recreate the scaffold logic using ValidateTrifectaUseCase structure or just plain logic.
    # Actually, UseCase logic for create is missing in imports, let's check imports.
    # ValidateTrifectaUseCase is for validate-trifecta command.
    # Create logic is typically simple file writing.

    # Re-implementing simplified create logic here to match previous state

    target_dir = path
    if not target_dir.exists():
        target_dir.mkdir(parents=True)

    config = TrifectaConfig(
        segment=segment,
        scope=scope,
        repo_root=str(path.absolute()),
        last_verified=time.strftime("%Y-%m-%d"),
        default_profile="impl_patch",
    )

    files = {
        "skill.md": template_renderer.render_skill(config),
        "readme_tf.md": template_renderer.render_readme(config),
        "_ctx/prime_" + segment + ".md": template_renderer.render_prime(config, []),
        "_ctx/agent.md": template_renderer.render_agent(config),
        "_ctx/session_" + segment + ".md": template_renderer.render_session(config),
    }

    try:
        for rel_path, content in files.items():
            full_path = target_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if (
                not full_path.exists()
            ):  # Don't overwrite unless force? Removed overwrite flag previously.
                full_path.write_text(content)

        # Verify line count of skill.md
        skill_lines = len(files["skill.md"].splitlines())
        if skill_lines > 100:
            raise ValueError(f"skill.md exceeds 100 lines ({skill_lines})")

        typer.echo(f"✅ Trifecta created at {target_dir}")
        for f in files:
            typer.echo(f"   ├── {f}")

        # Show quick commands from session
        typer.echo(
            files[f"_ctx/session_{segment}.md"].split("## Quick Commands (CLI)")[1].split("```")[1]
        )

    except Exception as e:
        typer.echo(_format_error(e, "Creation Error"), err=True)
        raise typer.Exit(1)


@app.command("validate-trifecta")
def validate_trifecta(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
) -> None:
    """
    Validate structure of a Trifecta Segment (files exist, YAML valid).

    TIP: Run this after creating or modifying a Trifecta pack.
    """
    _, file_system, _ = _get_dependencies(segment)
    use_case = ValidateTrifectaUseCase(file_system)

    # Validate path exists
    path = Path(segment)

    try:
        output = use_case.execute(path)
        typer.echo(output)
    except Exception as e:
        typer.echo(_format_error(e, "Validation Error"), err=True)
        raise typer.Exit(1)


@app.command("refresh-prime")
def refresh_prime(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
) -> None:
    """
    Regenerate `_ctx/prime_{segment}.md` with latest file list.

    TIP: The prime file is located at _ctx/prime_{segment}.md
    """
    template_renderer, file_system, _ = _get_dependencies(segment)
    use_case = RefreshPrimeUseCase(template_renderer, file_system)

    # Validate paths
    path = Path(segment).resolve()
    repo_root = path.parent if path.parent != path else path
    scan_path = path

    try:
        output = use_case.execute(path, scan_path, repo_root)
        typer.echo(output)
    except Exception as e:
        typer.echo(_format_error(e, "Refresh Error"), err=True)
        raise typer.Exit(1)


# =============================================================================
# Load Command (Plan A/B)
# =============================================================================


@app.command()
def load(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    task: str = typer.Option(..., "--task", "-t", help="Task description for context selection"),
    mode: str = typer.Option(
        "pcc", "--mode", "-m", help="Mode: pcc (Plan A) or fullfiles (Plan B)"
    ),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Macro command to load relevant context for a specific task.

    If context_pack.json exists, it uses Programmatic Context Calling (Plan A).
    Otherwise, it falls back to heuristic file selection (Plan B).
    """
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = MacroLoadUseCase(file_system, telemetry)

    try:
        target_path = Path(segment).resolve()
        if not target_path.exists():
            raise ValueError(f"Segment path does not exist: {target_path}")

        output = use_case.execute(target_path, task, mode=mode)
        typer.echo(output)
        telemetry.event(
            "load",
            {"segment": segment, "mode": mode},
            {"status": "ok"},
            int((time.time() - start_time) * 1000),
        )
    except Exception as e:
        telemetry.event(
            "load",
            {"segment": segment, "mode": mode},
            {"status": "error"},
            int((time.time() - start_time) * 1000),
        )
        typer.echo(_format_error(e, "Load Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()


# =============================================================================
# Session Commands
# =============================================================================


@session_app.command("append")
def session_append(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    summary: str = typer.Option(..., "--summary", help="Summary of work done"),
    files: str = typer.Option("", "--files", help="Comma-separated list of files touched"),
    commands: str = typer.Option("", "--commands", help="Comma-separated list of commands run"),
) -> None:
    """Append entry to session log (proactive logging without LLM)."""
    import hashlib
    from datetime import datetime, timezone

    segment_path = Path(segment).resolve()
    segment_name = segment_path.name
    session_file = segment_path / "_ctx" / f"session_{segment_name}.md"

    # Ensure _ctx directory exists
    (segment_path / "_ctx").mkdir(parents=True, exist_ok=True)

    # Get pack_sha if context_pack.json exists
    pack_sha = None
    pack_path = segment_path / "_ctx" / "context_pack.json"
    if pack_path.exists():
        try:
            content = pack_path.read_bytes()
            pack_sha = hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            pass

    # Parse CSV inputs
    files_list = [f.strip() for f in files.split(",") if f.strip()]
    commands_list = [c.strip() for c in commands.split(",") if c.strip()]

    # Create entry
    entry_lines = [
        f"## {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
        f"- **Summary**: {summary}",
    ]

    if files_list:
        entry_lines.append(f"- **Files**: {', '.join(files_list)}")

    if commands_list:
        entry_lines.append(f"- **Commands**: {', '.join(commands_list)}")

    if pack_sha:
        entry_lines.append(f"- **Pack SHA**: `{pack_sha}`")

    entry_lines.append("")  # Blank line after entry

    # Create or append to session file
    if not session_file.exists():
        # Create new file with header
        header = f"# Session Log - {segment_name}\n\n## History\n\n"
        session_file.write_text(header + "\n".join(entry_lines), encoding="utf-8")
        typer.echo(f"✅ Created {session_file.relative_to(segment_path)}")
    else:
        # Append to existing file
        with open(session_file, "a", encoding="utf-8") as f:
            f.write("\n".join(entry_lines) + "\n")
        typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")

    typer.echo(f"   Summary: {summary}")


if __name__ == "__main__":
    app()
