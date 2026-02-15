"""Trifecta CLI with T8 Telemetry."""

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Literal, Optional, Tuple

import click
import typer  # type: ignore
from click.exceptions import UsageError

# AST/LSP Integration (Phase 2a/2b)
from src.infrastructure.cli_ast import ast_app

from src.cli.invalid_option_handler import handle_invalid_option_error
from src.application.search_get_usecases import GetChunkUseCase, SearchUseCase
from src.application.telemetry_charts import generate_chart
from src.application.telemetry_health import run_health_check
from src.application.telemetry_reports import export_data, generate_report
from src.application.plan_use_case import PlanUseCase
from src.application.stub_regen_use_case import StubRegenUseCase
from src.application.pcc_metrics import parse_feature_map, evaluate_pcc, summarize_pcc
from src.application.use_cases import (
    BuildContextPackUseCase,
    MacroLoadUseCase,
    RefreshPrimeUseCase,
    StatsUseCase,
    ValidateContextPackUseCase,
    ValidateTrifectaUseCase,
)
from src.domain.models import TrifectaConfig

from src.infrastructure.file_system import FileSystemAdapter
from src.infrastructure.telemetry import Telemetry
from src.infrastructure.templates import TemplateRenderer
from src.application.obsidian_sync_use_case import create_sync_use_case
from src.infrastructure.obsidian_config import ObsidianConfigManager


class TrifectaGroup(typer.core.TyperGroup):
    """Custom Typer Group with enhanced error handling for invalid options."""

    def __call__(self, *args, **kwargs):
        """Override to catch and enhance invalid option errors."""
        try:
            return self.main(*args, **kwargs)
        except UsageError as e:
            # Handle invalid option errors with enhanced messaging
            error_msg = str(e)
            if "no such option" in error_msg.lower():
                enhanced_msg = handle_invalid_option_error(error_msg, sys.argv)
                typer.echo(enhanced_msg, err=True)
                sys.exit(2)
            # Re-raise other usage errors
            raise


app = typer.Typer(
    name="trifecta",
    help="Trifecta Context Engine v2.0 - Agentic Context Management (PCC).",
    rich_markup_mode="rich",
    cls=TrifectaGroup,
)

app.add_typer(ast_app, name="ast")

ctx_app = typer.Typer(
    help="Manage Trifecta Context Packs (ctx.search, ctx.get).",
    cls=TrifectaGroup,
)
session_app = typer.Typer(help="Session logging commands", cls=TrifectaGroup)
telemetry_app = typer.Typer(help="Telemetry analysis commands", cls=TrifectaGroup)
obsidian_app = typer.Typer(help="Obsidian vault integration for findings", cls=TrifectaGroup)

app.add_typer(ctx_app, name="ctx")
app.add_typer(session_app, name="session")
app.add_typer(telemetry_app, name="telemetry")
app.add_typer(obsidian_app, name="obsidian")

# Legacy Burn-Down
legacy_app = typer.Typer(help="Legacy Burn-Down commands", cls=TrifectaGroup)
app.add_typer(legacy_app, name="legacy")

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


def _get_lint_enabled(no_lint_flag: bool) -> bool:
    """Determine if linting should be enabled based on flag + env var.

    Precedence:
    1. --no-lint flag = True → disabled
    2. TRIFECTA_LINT env var = "0" or "false" → disabled
    3. TRIFECTA_LINT env var = "1" or "true" → enabled
    4. Default: DISABLED (conservative rollout)

    This allows gradual rollout without breaking existing workflows.
    """
    if no_lint_flag:
        return False
    env_val = os.environ.get("TRIFECTA_LINT", "").lower()
    if env_val in ("0", "false", "no"):
        return False
    if env_val in ("1", "true", "yes"):
        return True
    return False  # Conservative default: OFF until explicitly enabled


def _classify_north_star_precondition(errors: list[str]) -> str:
    """Classify structural precondition errors into stable Error Card codes."""
    if any("ambiguous" in err.lower() for err in errors):
        return "NORTH_STAR_AMBIGUOUS"
    if any("missing context file: _ctx/prime_" in err.lower() for err in errors):
        return "SEGMENT_NOT_INITIALIZED"
    return "NORTH_STAR_MISSING"


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
    from src.infrastructure.validators import (
        detect_legacy_context_files,
        validate_agents_constitution,
        validate_segment_structure_with_segment_id,
    )
    from src.infrastructure.segment_state import resolve_segment_state
    from src.application.exceptions import InvalidConfigScopeError, InvalidSegmentPathError
    from src.cli.error_cards import render_error_card

    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    try:
        state = resolve_segment_state(segment, file_system)
    except InvalidSegmentPathError as e:
        error_card = render_error_card(
            error_code="INVALID_SEGMENT_PATH",
            error_class="PRECONDITION",
            cause=str(e),
            next_steps=[
                "Verify the segment path exists and is a directory",
                "Use absolute path or run from the segment root",
            ],
            verify_cmd=f"trifecta ctx build -s {segment}",
        )
        telemetry.event(
            "ctx.build",
            {"segment": segment},
            {"status": "error", "error_code": "INVALID_SEGMENT_PATH"},
            int((time.time() - start_time) * 1000),
        )
        telemetry.flush()
        typer.echo(error_card, err=True)
        raise typer.Exit(code=1)
    except InvalidConfigScopeError as e:
        error_card = render_error_card(
            error_code="INVALID_CONFIG_SCOPE",
            error_class="PRECONDITION",
            cause=str(e),
            next_steps=[
                "Fix _ctx/trifecta_config.json repo_root to match segment root",
                "Or remove config and re-run create/sync",
            ],
            verify_cmd=f"trifecta ctx build -s {segment}",
        )
        telemetry.event(
            "ctx.build",
            {"segment": segment},
            {"status": "error", "error_code": "INVALID_CONFIG_SCOPE"},
            int((time.time() - start_time) * 1000),
        )
        telemetry.flush()
        typer.echo(error_card, err=True)
        raise typer.Exit(code=1)

    # FP Gate: North Star Strict Validation
    validation = validate_segment_structure_with_segment_id(
        state.segment_root_resolved, state.segment_id
    )
    if not validation.valid:
        errors = validation.errors
        code = _classify_north_star_precondition(errors)
        error_card = render_error_card(
            error_code=code,
            error_class="PRECONDITION",
            cause="; ".join(errors),
            next_steps=[
                "Ensure _ctx contains exactly one agent_*.md, prime_*.md, session_*.md",
                f"Expected suffix for this segment: {state.segment_id}",
            ],
            verify_cmd=f"trifecta ctx build -s {segment}",
        )
        typer.echo(error_card, err=True)
        telemetry.event(
            "ctx.build",
            {
                "segment": segment,
                "segment_id_resolved": state.segment_id,
                "segment_root_resolved": str(state.segment_root_resolved),
                "segment_state_source": state.source_of_truth,
            },
            {"status": "validation_failed", "error_code": code, "errors": len(errors)},
            int((time.time() - start_time) * 1000),
        )
        telemetry.flush()
        raise typer.Exit(code=1)
    else:
        # 1. Fail-Closed: AGENTS.md Constitution
        match validate_agents_constitution(state.segment_root_resolved):
            case Err(errors):
                typer.echo("❌ Constitution Failed (AGENTS.md):")
                for err in errors:
                    typer.echo(f"   - {err}")
                telemetry.event(
                    "ctx.build",
                    {"segment": segment},
                    {"status": "constitution_failed", "errors": len(errors)},
                    int((time.time() - start_time) * 1000),
                )
                telemetry.flush()
                raise typer.Exit(code=1)
            case Ok(_):
                pass

        # 2. Check for legacy file errors (Blocking)
        legacy = detect_legacy_context_files(state.segment_root_resolved)
        if legacy:
            typer.echo("❌ Legacy context files detected (Fail-Closed):")
            for lf in legacy:
                typer.echo(f"   - _ctx/{lf} (rename to suffix format: rule 3+1)")
            telemetry.event(
                "ctx.build",
                {"segment": segment},
                {"status": "legacy_files_error", "count": len(legacy)},
                int((time.time() - start_time) * 1000),
            )
            telemetry.flush()
            raise typer.Exit(code=1)

    use_case = BuildContextPackUseCase(file_system, telemetry)
    segment_fs = state.segment_root_resolved

    try:
        match use_case.execute(segment_fs):
            case Ok(pack):
                typer.echo(pack)
                telemetry.event(
                    "ctx.build",
                    {
                        "segment": segment,
                        "segment_id_resolved": state.segment_id,
                        "segment_root_resolved": str(state.segment_root_resolved),
                        "segment_state_source": state.source_of_truth,
                    },
                    {"status": "ok"},
                    int((time.time() - start_time) * 1000),
                )
            case Err(errors):
                typer.echo("❌ Build Failed:")
                for err in errors:
                    typer.echo(f"   - {err}")
                telemetry.event(
                    "ctx.build",
                    {
                        "segment": segment,
                        "segment_id_resolved": state.segment_id,
                        "segment_root_resolved": str(state.segment_root_resolved),
                        "segment_state_source": state.source_of_truth,
                    },
                    {"status": "build_error", "errors": len(errors)},
                    int((time.time() - start_time) * 1000),
                )
                telemetry.flush()
                raise typer.Exit(code=1)
    except Exception as e:
        telemetry.event(
            "ctx.build",
            {
                "segment": segment,
                "segment_id_resolved": state.segment_id,
                "segment_root_resolved": str(state.segment_root_resolved),
                "segment_state_source": state.source_of_truth,
            },
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
    no_lint: bool = typer.Option(
        False, "--no-lint", help="Disable query linting (anchor guidance expansion)"
    ),
) -> None:
    """Search for relevant chunks in the Context Pack.

    Query Processing Pipeline:
    1. Normalization: lowercase, strip, collapse whitespace
    2. Linting (optional): anchor-based classification + expansion for vague queries
    3. Tokenization: tokenize the FINAL query (post-linter)
    4. Alias Expansion: synonym-based expansion using _ctx/aliases.yaml
    5. Search: execute weighted search across all terms

    Controls:
      --no-lint              Disable linting for this search
      TRIFECTA_LINT=0/1       Env var to enable/disable globally
      Default: DISABLED (conservative rollout)

    To ENABLE linting: omit --no-lint flag or set TRIFECTA_LINT=1
    """
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = SearchUseCase(file_system, telemetry)

    try:
        # Determine if linting should be enabled (conservative default)
        enable_lint = _get_lint_enabled(no_lint)
        output = use_case.execute(
            Path(segment).resolve(), query, limit=limit, enable_lint=enable_lint
        )
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
    max_chunks: Optional[int] = typer.Option(
        None, "--max-chunks", help="Max chunks to retrieve (early-stop)"
    ),
    stop_on_evidence: bool = typer.Option(
        False, "--stop-on-evidence", help="Stop early when evidence found (feature flag)"
    ),
    query: Optional[str] = typer.Option(
        None, "--query", "-q", help="Query term for evidence matching"
    ),
    pd_report: bool = typer.Option(
        False, "--pd-report", help="Output parseable PD metrics line (for testing)"
    ),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Retrieve full content for specific chunks."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = GetChunkUseCase(file_system, telemetry)

    id_list = [x.strip() for x in ids.split(",") if x.strip()]

    # Agent-safe defaults: Check env vars if CLI flags not provided
    effective_max_chunks = max_chunks
    if effective_max_chunks is None:
        import os

        env_max_chunks = os.environ.get("TRIFECTA_PD_MAX_CHUNKS")
        if env_max_chunks:
            try:
                effective_max_chunks = int(env_max_chunks)
            except ValueError:
                pass  # Ignore invalid env var, use None

    effective_stop_on_evidence = stop_on_evidence
    if not effective_stop_on_evidence:
        import os

        env_stop_on_evidence = os.environ.get("TRIFECTA_PD_STOP_ON_EVIDENCE")
        if env_stop_on_evidence and env_stop_on_evidence == "1":
            effective_stop_on_evidence = True

    try:
        # Use execute_with_result when --pd-report is active for access to GetResult
        if pd_report:
            output, result = use_case.execute_with_result(
                Path(segment).resolve(),
                id_list,
                mode=mode,
                budget_token_est=budget_token_est,
                max_chunks=effective_max_chunks,
                stop_on_evidence=effective_stop_on_evidence,
                query=query,
            )
            typer.echo(output)

            # Emit PD_REPORT with version and invariant keys
            strong_hit = 1 if result.evidence_metadata.get("strong_hit") else 0
            support = 1 if result.evidence_metadata.get("support") else 0
            typer.echo(
                f"PD_REPORT v=1 "
                f"stop_reason={result.stop_reason} "
                f"chunks_returned={result.chunks_returned} "
                f"chunks_requested={result.chunks_requested} "
                f"chars_returned_total={result.chars_returned_total} "
                f"strong_hit={strong_hit} "
                f"support={support}"
            )
        else:
            # Standard path: just get output string
            output = use_case.execute(
                Path(segment).resolve(),
                id_list,
                mode=mode,
                budget_token_est=budget_token_est,
                max_chunks=effective_max_chunks,
                stop_on_evidence=effective_stop_on_evidence,
                query=query,
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
        result = use_case.execute(Path(segment).resolve())
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


@ctx_app.command("stats")
def stats(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    window: int = typer.Option(0, "--window", "-w", help="Days to look back (0 = all)"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Show telemetry statistics for the segment."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = StatsUseCase(file_system, telemetry)

    try:
        result = use_case.execute(Path(segment), window=window)

        # Format output
        lines = []
        lines.append("╭" + "─" * 50 + "╮")
        lines.append("│" + " " * 15 + "Trifecta Stats" + " " * 23 + "│")
        lines.append(
            f"│           Last {window} days"
            if window > 0
            else "│                  All time" + " " * 22 + "│"
        )
        lines.append("╰" + "─" * 50 + "╯")
        lines.append("")

        # Summary
        summary = result["summary"]
        lines.append("Summary")
        lines.append("─" * 50)
        lines.append(f"  Total searches:      {summary['total_searches']}")
        lines.append(f"  Hits:                {summary['hits']}")
        lines.append(f"  Zero hits:           {summary['zero_hits']}")
        lines.append(f"  Hit rate:            {summary['hit_rate']}%")
        lines.append(f"  Avg latency:         {summary['avg_latency_ms']:.1f}ms")
        lines.append("")

        # Top zero-hit queries
        lines.append("Top Zero-Hit Queries")
        lines.append("─" * 50)
        for item in result["top_zero_hit_queries"][:10]:
            lines.append(f"  [{item['count']:2d}] {item['query'][:50]}")
        lines.append("")

        # Query type breakdown
        lines.append("Query Type Breakdown")
        lines.append("─" * 50)
        total = sum(result["query_type_breakdown"].values())
        for qtype in ["meta", "impl", "unknown"]:
            count = result["query_type_breakdown"].get(qtype, 0)
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"  {qtype:<10} {count:>3}  ({pct:>5.1f}%)")
        lines.append("")

        # Hit target breakdown
        if result["hit_target_breakdown"]:
            lines.append("Hit Target Breakdown")
            lines.append("─" * 50)
            total_hits = sum(result["hit_target_breakdown"].values())
            for target, count in sorted(
                result["hit_target_breakdown"].items(), key=lambda x: -x[1]
            ):
                pct = count / total_hits * 100 if total_hits > 0 else 0
                lines.append(f"  {target:<10} {count:>3}  ({pct:>5.1f}%)")
            lines.append("")

        typer.echo("\n".join(lines))
        telemetry.observe("ctx.stats", int((time.time() - start_time) * 1000))

    except Exception as e:
        telemetry.event(
            "ctx.stats", {}, {"status": "error"}, int((time.time() - start_time) * 1000)
        )
        typer.echo(_format_error(e, "Stats Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()


@ctx_app.command("plan")
def plan(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    task: str = typer.Option(..., "--task", "-t", help="Task description to plan"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Generate execution plan using PRIME index (no RAG)."""
    telemetry = _get_telemetry(segment, telemetry_level)
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = PlanUseCase(file_system, telemetry)

    try:
        result = use_case.execute(Path(segment).resolve(), task)

        if json_output:
            typer.echo(json.dumps(result, indent=2))
        else:
            # Human-readable output
            lines = []
            lines.append("╭" + "─" * 50 + "╮")
            lines.append("│" + " " * 12 + "Execution Plan" + " " * 24 + "│")
            lines.append("╰" + "─" * 50 + "╯")
            lines.append("")

            status = "✅ HIT" if result["plan_hit"] else "⚠️ NO HIT"
            lines.append(f"Status: {status}")
            lines.append("")

            if result["selected_feature"]:
                lines.append(f"Selected Feature: {result['selected_feature']}")
            else:
                lines.append("Selected Feature: (none - using entrypoints)")
            lines.append("")

            if result["chunk_ids"]:
                lines.append(f"Chunk IDs: {', '.join(result['chunk_ids'][:3])}")
                lines.append(f"            ... ({len(result['chunk_ids'])} total)")
            else:
                lines.append("Chunk IDs: (none)")
            lines.append("")

            if result["paths"]:
                lines.append(f"Paths: {', '.join(result['paths'][:3])}")
                if len(result["paths"]) > 3:
                    lines.append(f"       ... ({len(result['paths'])} total)")
            else:
                lines.append("Paths: (entrypoints)")
            lines.append("")

            lines.append("Next Steps:")
            for i, step in enumerate(result["next_steps"], 1):
                lines.append(f"  {i}. {step['action'].capitalize()}: {step['target']}")
            lines.append("")

            budget = result["budget_est"]
            lines.append(f"Budget Estimate: ~{budget['tokens']} tokens")
            lines.append(f"  ({budget['why']})")
            lines.append("")

            typer.echo("\n".join(lines))

    except Exception as e:
        typer.echo(_format_error(e, "Plan Error"), err=True)
        raise typer.Exit(1)


@ctx_app.command("eval-plan")
def eval_plan(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    dataset: str = typer.Option(
        "docs/plans/t9_plan_eval_tasks.md",
        "--dataset",
        "-d",
        help="Path to evaluation dataset markdown file",
    ),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show per-task breakdown"),
) -> None:
    """Evaluate ctx.plan against a dataset of tasks."""
    import hashlib
    import re
    from datetime import datetime

    telemetry = _get_telemetry(segment, telemetry_level)
    _, file_system, _ = _get_dependencies(segment, telemetry)

    # Load PRIME for PCC metrics
    segment_path = Path(segment).resolve()
    prime_files = list(segment_path.glob("_ctx/prime_*.md"))
    prime_path = prime_files[0] if prime_files else None
    feature_map = {}
    if prime_path:
        try:
            feature_map = parse_feature_map(prime_path)
        except Exception as e:
            typer.echo(f"⚠️  PCC Metrics: Failed to parse feature_map from {prime_path.name}")
            typer.echo(f"   Error: {e}")
            typer.echo("   PCC metrics will be disabled for this run.")
            typer.echo("")

    # Load dataset from markdown
    dataset_path = Path(dataset).resolve()
    if not dataset_path.exists():
        typer.echo(f"❌ Dataset file not found: {dataset_path}")
        raise typer.Exit(1)

    content = dataset_path.read_text()

    # Dataset identity for anti-gaming (T9.3.1)
    dataset_sha256 = hashlib.sha256(content.encode()).hexdigest()[:16]
    dataset_mtime = datetime.fromtimestamp(dataset_path.stat().st_mtime).isoformat()

    # Extract tasks from markdown (quoted strings after numbers)
    tasks = re.findall(r'^\d+\.\s+"([^"]+)"', content, re.MULTILINE)

    # Parse expected_feature_id from dataset (T9.3.2)
    # Format: number. "task" | expected_feature_id | notes
    expected_features = {}
    for line in content.split("\n"):
        match = re.match(r'^\d+\.\s+"([^"]+)"\s*\|\s*(\w+)', line)
        if match:
            task_str = match.group(1)
            expected_id = match.group(2)
            expected_features[task_str] = expected_id

    if not tasks:
        typer.echo("❌ No tasks found in dataset file")
        raise typer.Exit(1)

    # Run evaluation
    use_case = PlanUseCase(file_system, telemetry)

    results = []
    feature_count = 0
    nl_trigger_count = 0
    alias_count = 0
    fallback_count = 0
    true_zero_count = 0
    correct_predictions = 0  # T9.3.2: plan_accuracy_top1
    pcc_metrics_rows = []  # PCC metrics per task

    for i, task in enumerate(tasks, 1):
        result = use_case.execute(Path(segment), task)
        results.append({"task_id": i, "task": task, "result": result})

        # Classify outcome (T9.3.2: 4-level hierarchy)
        selected_by = result.get("selected_by", "fallback")

        if selected_by == "feature":
            feature_count += 1
        elif selected_by == "nl_trigger":
            nl_trigger_count += 1
        elif selected_by == "alias":
            alias_count += 1
        else:  # fallback
            fallback_count += 1

        # T9.3.2: Track accuracy if expected_feature_id is available
        expected_id = expected_features.get(task)
        selected_id = result.get("selected_feature")

        if expected_id:
            if expected_id == "fallback":
                # Correct if selected_feature is None
                if selected_id is None:
                    correct_predictions += 1
            elif selected_id == expected_id:
                # Correct if selected_feature matches expected
                correct_predictions += 1
        # Check for true_zero_guidance (bug condition)
        chunks_count = len(result.get("chunk_ids", []))
        paths_count = len(result.get("paths", []))
        # entrypoints_count calculation removed (unused)
        next_steps_count = len(result.get("next_steps", []))

        if chunks_count == 0 and paths_count == 0 and next_steps_count == 0:
            true_zero_count += 1

        # Compute PCC metrics if feature_map is available
        if feature_map and expected_id:
            pcc_row = evaluate_pcc(
                expected_feature=expected_id,
                predicted_feature=selected_id,
                predicted_paths=result.get("paths", []),
                feature_map=feature_map,
                selected_by=selected_by,
            )
            pcc_metrics_rows.append(pcc_row)

    total = len(tasks)
    expected_count = len(expected_features)  # T9.3.2: Number of labeled tasks

    # Compute rates (T9.3.2: 4-level hierarchy)
    feature_hit_rate = (feature_count / total * 100) if total > 0 else 0
    nl_trigger_hit_rate = (nl_trigger_count / total * 100) if total > 0 else 0
    alias_hit_rate = (alias_count / total * 100) if total > 0 else 0
    fallback_rate = (fallback_count / total * 100) if total > 0 else 0
    true_zero_guidance_rate = (true_zero_count / total * 100) if total > 0 else 0

    # T9.3.2: Compute accuracy if expected labels exist
    plan_accuracy_top1 = (
        (correct_predictions / expected_count * 100) if expected_count > 0 else None
    )

    # Compute PCC summary
    pcc_summary = summarize_pcc(pcc_metrics_rows) if pcc_metrics_rows else {}

    # Output report
    typer.echo("=" * 80)
    typer.echo("EVALUATION REPORT: ctx.plan")
    typer.echo("=" * 80)
    typer.echo("")
    typer.echo(f"Dataset: {dataset_path}")
    typer.echo(f"Dataset SHA256: {dataset_sha256}")
    typer.echo(f"Dataset mtime: {dataset_mtime}")
    typer.echo(f"Segment: {segment}")
    typer.echo(f"Total tasks: {total}")
    typer.echo("")
    typer.echo(f"Dataset: {dataset_path}")
    typer.echo(f"Dataset SHA256: {dataset_sha256}")
    typer.echo(f"Dataset mtime: {dataset_mtime}")
    typer.echo(f"Segment: {segment}")
    typer.echo(f"Total tasks: {total}")
    typer.echo("")

    typer.echo(f"Distribution (MUST SUM TO {total}):")
    typer.echo(f"  feature (L1):   {feature_count} ({feature_hit_rate:.1f}%)")
    typer.echo(f"  nl_trigger (L2): {nl_trigger_count} ({nl_trigger_hit_rate:.1f}%)")
    typer.echo(f"  alias (L3):      {alias_count} ({alias_hit_rate:.1f}%)")
    typer.echo(f"  fallback (L4):   {fallback_count} ({fallback_rate:.1f}%)")
    typer.echo("  ─────────────────────────────")
    typer.echo(f"  total:          {total} (100.0%)")
    typer.echo("")

    typer.echo("Computed Rates:")
    typer.echo(f"  feature_hit_rate:       {feature_hit_rate:.1f}%")
    typer.echo(f"  nl_trigger_hit_rate:    {nl_trigger_hit_rate:.1f}%")
    typer.echo(f"  alias_hit_rate:         {alias_hit_rate:.1f}%")
    typer.echo(f"  fallback_rate:          {fallback_rate:.1f}%")
    typer.echo(f"  true_zero_guidance_rate: {true_zero_guidance_rate:.1f}%")

    # T9.3.2: Show accuracy if expected labels exist
    if plan_accuracy_top1 is not None:
        typer.echo(
            f"  plan_accuracy_top1:     {plan_accuracy_top1:.1f}% ({correct_predictions}/{expected_count} correct)"
        )
    typer.echo("")

    # PCC Metrics (if feature_map is available)
    if pcc_summary:
        typer.echo("PCC Metrics:")
        typer.echo(f"  path_correct_count:    {pcc_summary['path_correct_count']}")
        typer.echo(f"  false_fallback_count:  {pcc_summary['false_fallback_count']}")
        typer.echo(f"  safe_fallback_count:   {pcc_summary['safe_fallback_count']}")
        typer.echo("")

    # Verbose per-task table
    if verbose:
        typer.echo("Per-Task Breakdown:")
        typer.echo("─" * 80)
        for item in results:
            tid = item["task_id"]
            task_short = item["task"][:40] + "..." if len(item["task"]) > 40 else item["task"]
            result = item["result"]
            outcome = result.get("selected_by", "fallback")
            feature = result.get("selected_feature", "N/A")
            match_terms = result.get("match_terms_count", 0)
            chunks = len(result.get("chunk_ids", []))
            paths = len(result.get("paths", []))

            typer.echo(f"{tid:2d}. [{outcome:8s}] {task_short}")
            typer.echo(f"    → feature:{feature} terms:{match_terms} chunks:{chunks} paths:{paths}")
        typer.echo("")

    # Top missed tasks (fallback)
    missed = [r for r in results if r["result"].get("selected_by") == "fallback"]
    if missed:
        typer.echo(f"Top Missed Tasks (fallback): {len(missed)} total")
        for i, item in enumerate(missed[:10], 1):
            task_short = item["task"][:60] + "..." if len(item["task"]) > 60 else item["task"]
            typer.echo(f"  {i}. {task_short}")
        typer.echo("")

    # Examples of hits
    hits = [r for r in results if r["result"].get("plan_hit")]
    if hits:
        typer.echo("Examples (hits with selected_feature):")
        for i, item in enumerate(hits[:5], 1):
            task_short = item["task"][:50] + "..." if len(item["task"]) > 50 else item["task"]
            result = item["result"]
            outcome = result.get("selected_by", "unknown")
            feature = result.get("selected_feature", "N/A")
            chunks = len(result.get("chunk_ids", []))
            paths = len(result.get("paths", []))
            typer.echo(f"  {i}. [{outcome}] '{task_short}'")
            typer.echo(f"     → {feature} ({chunks} chunks, {paths} paths)")
            if i >= 3:
                break

    typer.echo("")

    # Determine gate type based on dataset name (T9.3.1)
    is_l1_dataset = "_l1" in dataset_path.name.lower()
    gate_name = "Gate-L1" if is_l1_dataset else "Gate-NL"

    # Gate decision (T9.3.1: separate gates for NL and L1)
    go_criteria = []
    no_go_reasons = []

    if is_l1_dataset:
        # Gate-L1 criteria (explicit feature:<id> tests)
        if feature_hit_rate >= 95:
            go_criteria.append(f"feature_hit_rate {feature_hit_rate:.1f}% >= 95%")
        else:
            no_go_reasons.append(f"feature_hit_rate {feature_hit_rate:.1f}% < 95%")

        if fallback_rate <= 5:
            go_criteria.append(f"fallback_rate {fallback_rate:.1f}% <= 5%")
        else:
            no_go_reasons.append(f"fallback_rate {fallback_rate:.1f}% > 5%")

        if true_zero_guidance_rate == 0:
            go_criteria.append(f"true_zero_guidance_rate {true_zero_guidance_rate:.1f}% = 0%")
        else:
            no_go_reasons.append(f"true_zero_guidance_rate {true_zero_guidance_rate:.1f}% > 0%")
    else:
        # Gate-NL criteria (natural language generalization)
        if fallback_rate < 20:
            go_criteria.append(f"fallback_rate {fallback_rate:.1f}% < 20%")
        else:
            no_go_reasons.append(f"fallback_rate {fallback_rate:.1f}% >= 20%")

        if true_zero_guidance_rate == 0:
            go_criteria.append(f"true_zero_guidance_rate {true_zero_guidance_rate:.1f}% = 0%")
        else:
            no_go_reasons.append(f"true_zero_guidance_rate {true_zero_guidance_rate:.1f}% > 0%")

        if alias_hit_rate <= 70:
            go_criteria.append(f"alias_hit_rate {alias_hit_rate:.1f}% <= 70%")
        else:
            no_go_reasons.append(f"alias_hit_rate {alias_hit_rate:.1f}% > 70%")

        # Informative for NL (not required)
        if feature_hit_rate >= 10:
            go_criteria.append(f"feature_hit_rate {feature_hit_rate:.1f}% >= 10% (informative)")
        else:
            no_go_reasons.append(f"feature_hit_rate {feature_hit_rate:.1f}% < 10% (informative)")

    if go_criteria and not no_go_reasons:
        typer.echo(f"✅ GO ({gate_name}): All criteria passed")
        for c in go_criteria:
            typer.echo(f"   ✓ {c}")
    else:
        typer.echo(f"❌ NO-GO ({gate_name}): Some criteria failed")
        for r in no_go_reasons:
            typer.echo(f"   ✗ {r}")
        if go_criteria:
            typer.echo("")
            typer.echo("Passed criteria:")
            for c in go_criteria:
                typer.echo(f"   ✓ {c}")

    telemetry.flush()


@ctx_app.command("sync")
def sync(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Macro: Build + Validate."""
    from src.application.exceptions import (
        InvalidConfigScopeError,
        InvalidSegmentPathError,
        PrimeFileNotFoundError,
    )
    from src.cli.error_cards import render_error_card
    from src.infrastructure.segment_state import resolve_segment_state
    from src.infrastructure.validators import validate_segment_structure_with_segment_id

    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    try:
        state = resolve_segment_state(segment, file_system)
    except InvalidSegmentPathError as e:
        error_card = render_error_card(
            error_code="INVALID_SEGMENT_PATH",
            error_class="PRECONDITION",
            cause=str(e),
            next_steps=[
                "Verify the segment path exists and is a directory",
                "Use absolute path or run from the segment root",
            ],
            verify_cmd=f"trifecta ctx sync -s {segment}",
        )
        telemetry.event(
            "ctx.sync",
            {"segment": segment},
            {"status": "error", "error_code": "INVALID_SEGMENT_PATH"},
            int((time.time() - start_time) * 1000),
        )
        telemetry.flush()
        typer.echo(error_card, err=True)
        raise typer.Exit(1)
    except InvalidConfigScopeError as e:
        error_card = render_error_card(
            error_code="INVALID_CONFIG_SCOPE",
            error_class="PRECONDITION",
            cause=str(e),
            next_steps=[
                "Fix _ctx/trifecta_config.json repo_root to match segment root",
                "Or remove config and re-run create/sync",
            ],
            verify_cmd=f"trifecta ctx sync -s {segment}",
        )
        telemetry.event(
            "ctx.sync",
            {"segment": segment},
            {"status": "error", "error_code": "INVALID_CONFIG_SCOPE"},
            int((time.time() - start_time) * 1000),
        )
        telemetry.flush()
        typer.echo(error_card, err=True)
        raise typer.Exit(1)

    validation = validate_segment_structure_with_segment_id(
        state.segment_root_resolved, state.segment_id
    )
    if not validation.valid:
        errors = validation.errors
        code = _classify_north_star_precondition(errors)
        if code == "SEGMENT_NOT_INITIALIZED":
            next_steps = [
                f"trifecta create -s {segment}",
                f"trifecta refresh-prime -s {segment}",
            ]
        else:
            next_steps = [
                "Ensure _ctx contains exactly one agent_*.md, prime_*.md, session_*.md",
                f"Expected suffix for this segment: {state.segment_id}",
            ]
        error_card = render_error_card(
            error_code=code,
            error_class="PRECONDITION",
            cause="; ".join(errors),
            next_steps=next_steps,
            verify_cmd=f"trifecta ctx sync -s {segment}",
        )
        telemetry.event(
            "ctx.sync",
            {
                "segment": segment,
                "segment_id_resolved": state.segment_id,
                "segment_root_resolved": str(state.segment_root_resolved),
                "segment_state_source": state.source_of_truth,
            },
            {"status": "error", "error_code": code, "errors": len(errors)},
            int((time.time() - start_time) * 1000),
        )
        telemetry.flush()
        typer.echo(error_card, err=True)
        raise typer.Exit(1)

    try:
        typer.echo("🔄 Running build...")
        build_uc = BuildContextPackUseCase(file_system, telemetry)
        build_uc.execute(state.segment_root_resolved)

        typer.echo("✅ Build complete. Validating...")
        validate_uc = ValidateContextPackUseCase(file_system, telemetry)
        result = validate_uc.execute(state.segment_root_resolved)

        # Format ValidationResult for display
        if result.passed:
            output = "✅ Validation Passed"
            if result.warnings:
                output += "\n\n⚠️  Warnings:\n" + "\n".join(f"   - {w}" for w in result.warnings)
        else:
            output = "❌ Validation Failed\n\n" + "\n".join(f"   - {e}" for e in result.errors)

        typer.echo(output)

        if result.passed:
            # Regenerate stubs
            typer.echo("🔄 Regenerating stubs...")
            stub_regen_uc = StubRegenUseCase(telemetry)
            stub_result = stub_regen_uc.execute(state.segment_root_resolved)

            if stub_result["stubs"]:
                typer.echo(f"   ✅ Regenerated: {', '.join(stub_result['stubs'])}")

            if stub_result["warnings"]:
                typer.echo("   ⚠️  Warnings:")
                for w in stub_result["warnings"]:
                    typer.echo(f"      - {w}")

            if not stub_result["regen_ok"]:
                typer.echo("   ⚠️  Stub regeneration had errors:")
                for err in stub_result["errors"]:
                    typer.echo(f"      - {err}")

        telemetry.event(
            "ctx.sync",
            {
                "segment": segment,
                "segment_id_resolved": state.segment_id,
                "segment_root_resolved": str(state.segment_root_resolved),
                "segment_state_source": state.source_of_truth,
            },
            {"status": "ok"},
            int((time.time() - start_time) * 1000),
        )

        if not result.passed:
            raise typer.Exit(code=1)

    except Exception as e:
        if isinstance(e, PrimeFileNotFoundError):
            error_card = render_error_card(
                error_code="SEGMENT_NOT_INITIALIZED",
                error_class="PRECONDITION",
                cause=f"Missing prime file: {e.expected_path}",
                next_steps=[
                    f"trifecta create -s {segment}",
                    f"trifecta refresh-prime -s {segment}",
                ],
                verify_cmd=f"trifecta ctx sync -s {segment}",
            )
            telemetry.event(
                "ctx.sync",
                {
                    "segment": segment,
                    "segment_id_resolved": state.segment_id,
                    "segment_root_resolved": str(state.segment_root_resolved),
                    "segment_state_source": state.source_of_truth,
                },
                {"status": "error", "error_code": "SEGMENT_NOT_INITIALIZED"},
                int((time.time() - start_time) * 1000),
            )
            typer.echo(error_card, err=True)
            raise typer.Exit(1)

        # Substring fallback for backward compatibility (deprecated)
        elif isinstance(e, FileNotFoundError) and "Expected prime file not found" in str(e):
            from src.infrastructure.deprecations import maybe_emit_deprecated

            # Track deprecated usage (policy: off|warn|fail via env var)
            maybe_emit_deprecated("fallback_prime_missing_string_match", telemetry)

            # Emit deprecation warning for harness detection (legacy)
            typer.echo("TRIFECTA_DEPRECATED: fallback_prime_missing_string_match_used", err=True)

            error_card = render_error_card(
                error_code="SEGMENT_NOT_INITIALIZED",
                error_class="PRECONDITION",
                cause=str(e),
                next_steps=[
                    f"trifecta create -s {segment}",
                    f"trifecta refresh-prime -s {segment}",
                ],
                verify_cmd=f"trifecta ctx sync -s {segment}",
            )
            telemetry.event(
                "ctx.sync",
                {
                    "segment": segment,
                    "segment_id_resolved": state.segment_id,
                    "segment_root_resolved": str(state.segment_root_resolved),
                    "segment_state_source": state.source_of_truth,
                },
                {"status": "error", "error_code": "SEGMENT_NOT_INITIALIZED"},
                int((time.time() - start_time) * 1000),
            )
            typer.echo(error_card, err=True)
            raise typer.Exit(1)

        # All other exceptions (fail-closed)
        else:
            telemetry.event(
                "ctx.sync",
                {
                    "segment": segment,
                    "segment_id_resolved": state.segment_id,
                    "segment_root_resolved": str(state.segment_root_resolved),
                    "segment_state_source": state.source_of_truth,
                },
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
                "⚠️  WARNING: This will overwrite skill.md, _ctx/agent_<segment>.md, _ctx/prime_<segment>.md, _ctx/session_<segment>.md, readme_tf.md"
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

        segment_id = config.segment_id
        (Path(segment) / "skill.md").write_text(template_renderer.render_skill(config))
        (Path(segment) / "_ctx" / f"agent_{segment_id}.md").write_text(
            template_renderer.render_agent(config)
        )
        (Path(segment) / "_ctx" / f"prime_{segment_id}.md").write_text(
            template_renderer.render_prime(config, [])
        )
        (Path(segment) / "_ctx" / f"session_{segment_id}.md").write_text(
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
    segment: str = typer.Option(..., "--segment", "-s", help="Path to segment directory"),
    scope: str = typer.Option("Scope", "--scope", help="Short description of segment scope"),
) -> None:
    """
    Scaffold a new Trifecta Segment.

    Generates:
    - skill.md (Rules & Roles)
    - _ctx/prime_{segment}.md (Reading list)
    - _ctx/agent_{segment}.md (Tech stack)
    - _ctx/session_{segment}.md (Runbook)
    - _ctx/trifecta_config.json (SSOT segment config)
    - AGENTS.md (Constitution gate seed)
    - readme_tf.md (Documentation)

    Postcondition:
    - Segment is left in state SCAFFOLDED+CONFIGURED:
      `ctx build` and `ctx reset --force` must not fail due to missing bootstrap artifacts.
    """
    # FIXED: -s is now path to target directory (consistent with ctx sync/search/get)
    # Segment ID derived from directory name
    target_dir = Path(segment).resolve()

    template_renderer, _, _ = _get_dependencies(str(target_dir))
    telemetry = _get_telemetry(str(target_dir), "lite")
    start_time = time.time()

    if not target_dir.exists():
        target_dir.mkdir(parents=True)

    # Derive segment_id from directory name (same logic as use_cases.py)
    from src.domain.segment_resolver import get_segment_slug

    segment_id = get_segment_slug(target_dir)

    config = TrifectaConfig(
        segment=segment_id,
        scope=scope,
        repo_root=str(target_dir),
        last_verified=time.strftime("%Y-%m-%d"),
        default_profile="impl_patch",
    )

    files = {
        "AGENTS.md": "# AGENTS\n\nRead skill.md and _ctx files before running commands.\n",
        "skill.md": template_renderer.render_skill(config),
        "readme_tf.md": template_renderer.render_readme(config),
        f"_ctx/prime_{segment_id}.md": template_renderer.render_prime(config, []),
        f"_ctx/agent_{segment_id}.md": template_renderer.render_agent(config),
        f"_ctx/session_{segment_id}.md": template_renderer.render_session(config),
        "_ctx/trifecta_config.json": json.dumps(config.model_dump(), indent=2) + "\n",
    }

    try:
        for rel_path, content in files.items():
            full_path = target_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if (
                not full_path.exists()
            ):  # Don't overwrite unless force? Removed overwrite flag previously.
                full_path.write_text(content)

        required_bootstrap = [
            target_dir / "AGENTS.md",
            target_dir / "skill.md",
            target_dir / "_ctx" / "trifecta_config.json",
            target_dir / "_ctx" / f"agent_{segment_id}.md",
            target_dir / "_ctx" / f"prime_{segment_id}.md",
            target_dir / "_ctx" / f"session_{segment_id}.md",
        ]
        missing_bootstrap = [
            str(p.relative_to(target_dir)) for p in required_bootstrap if not p.exists()
        ]

        # Verify line count of skill.md
        skill_lines = len(files["skill.md"].splitlines())
        if skill_lines > 100:
            raise ValueError(f"skill.md exceeds 100 lines ({skill_lines})")

        typer.echo(f"✅ Trifecta created at {target_dir}")
        for f in files:
            typer.echo(f"   ├── {f}")

        # Show quick commands from session
        typer.echo(
            files[f"_ctx/session_{segment_id}.md"]
            .split("## Quick Commands (CLI)")[1]
            .split("```")[1]
        )
        telemetry.event(
            "ctx.create",
            {
                "segment": str(target_dir),
                "segment_bootstrap_version": 2,
            },
            {
                "status": "ok",
                "bootstrap_missing_artifacts_count": len(missing_bootstrap),
            },
            int((time.time() - start_time) * 1000),
        )

    except Exception as e:
        telemetry.event(
            "ctx.create",
            {
                "segment": str(target_dir),
                "segment_bootstrap_version": 2,
            },
            {"status": "error"},
            int((time.time() - start_time) * 1000),
        )
        typer.echo(_format_error(e, "Creation Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()


@app.command("validate-trifecta", hidden=True, help="[DEPRECATED] Use 'ctx validate' instead.")
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


@app.command("refresh-prime", hidden=True, help="[DEPRECATED] Use 'ctx sync' instead.")
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


# =============================================================================
# Telemetry Commands
# =============================================================================


@telemetry_app.command("report")
def telemetry_report(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    last: int = typer.Option(7, "--last", help="Last N days (0 = all)"),
    format_type: str = typer.Option("table", "--format", help="Output format: table, json"),
) -> None:
    """Generate telemetry report."""
    segment_path = Path(segment).resolve()

    report = generate_report(segment_path, last, format_type)
    typer.echo(report)


@telemetry_app.command("export")
def telemetry_export(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    format_type: str = typer.Option("json", "--format", help="Export format: json, csv"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export telemetry data."""
    segment_path = Path(segment).resolve()
    output_path = Path(output) if output else None

    data = export_data(segment_path, format_type, output_path)

    if output_path:
        typer.echo(f"✅ Exported to {output_path}")
    else:
        typer.echo(data)


@telemetry_app.command("chart")
def telemetry_chart(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    chart_type: str = typer.Option("hits", "--type", help="Chart type: hits, latency, commands"),
    days: int = typer.Option(7, "--days", help="Last N days"),
) -> None:
    """Generate ASCII chart."""
    segment_path = Path(segment).resolve()

    chart = generate_chart(segment_path, chart_type, days)
    typer.echo(chart)


@telemetry_app.command("health")
def telemetry_health(
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
) -> None:
    """Check telemetry health. Exit codes: 0=OK, 2=WARN, 3=FAIL."""
    segment_path = Path(segment).resolve()
    exit_code = run_health_check(segment_path)
    raise typer.Exit(code=exit_code)


@legacy_app.command("scan")
def legacy_scan(
    path: str = typer.Option(".", "--path", "-p", help="Root path to scan"),
) -> None:
    """Scan for undeclared legacy code. Fails if new legacy appears."""
    from src.application.legacy_use_case import scan_legacy
    from src.domain.result import Err, Ok

    repo_root = Path(path).resolve()
    manifest_path = repo_root / "docs/legacy_manifest.json"

    typer.echo(f"🔍 Scanning for legacy debt in {repo_root}...")
    typer.echo(f"   Manifest: {manifest_path}")

    match scan_legacy(repo_root, manifest_path):
        case Ok(legacy_items):
            typer.echo("✅ Legacy Check Passed.")
            if legacy_items:
                typer.echo(f"   Found {len(legacy_items)} declared legacy items (Technical Debt).")
            else:
                typer.echo("   Zero legacy debt found!")
        case Err(errors):
            typer.echo("❌ Legacy Check Failed (Undeclared Debt):")
            for err in errors:
                typer.echo(f"   - {err}")
            raise typer.Exit(code=1)


# =============================================================================
# Obsidian Integration Commands
# =============================================================================


@obsidian_app.command("sync")
def obsidian_sync(
    segment: str = typer.Option(".", "--segment", "-s", help=HELP_SEGMENT),
    vault_path: Optional[str] = typer.Option(
        None, "--vault-path", "-v", help="Obsidian vault path"
    ),
    min_priority: str = typer.Option("P5", "--min-priority", "-p", help="Minimum priority (P1-P5)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing"),
    include_hookify: bool = typer.Option(
        True, "--include-hookify/--no-hookify", help="Include hookify violations"
    ),
    include_telemetry: bool = typer.Option(
        True, "--include-telemetry/--no-telemetry", help="Include telemetry anomalies"
    ),
    include_micro_audit: bool = typer.Option(
        True, "--include-micro-audit/--no-micro-audit", help="Include micro-audit report findings"
    ),
) -> None:
    """Sync findings to Obsidian vault as atomic notes."""
    segment_path = Path(segment).expanduser().resolve()

    # Validate priority
    valid_priorities = {"P1", "P2", "P3", "P4", "P5"}
    if min_priority not in valid_priorities:
        typer.echo(f"❌ Invalid priority: {min_priority}. Must be one of {valid_priorities}")
        raise typer.Exit(code=1)

    # Create use case with config
    try:
        use_case = create_sync_use_case(
            vault_path=Path(vault_path).expanduser() if vault_path else None,
            min_priority=min_priority,  # type: ignore
        )
    except Exception as e:
        typer.echo(f"❌ Configuration error: {e}")
        typer.echo("\n💡 Tip: Run 'trifecta obsidian config --vault-path <path>' first")
        raise typer.Exit(code=1)

    # Execute sync
    sources = {
        "hookify": include_hookify,
        "telemetry": include_telemetry,
        "micro_audit": include_micro_audit,
    }

    try:
        result = use_case.execute(
            segment_path=segment_path,
            min_priority=min_priority,  # type: ignore
            dry_run=dry_run,
            sources=sources,
        )
    except RuntimeError as e:
        typer.echo(f"❌ Sync failed: {e}")
        raise typer.Exit(code=1)

    # Show summary
    typer.echo("\n✨ Sync complete!")
    typer.echo(
        f"  Sources: {', '.join(result.active_sources) if result.active_sources else 'None'}"
    )
    typer.echo(f"  Findings: {result.total_findings}")
    typer.echo(f"  Notes created: {result.notes_created}")
    typer.echo(f"  Notes updated: {result.notes_updated}")
    typer.echo(f"  Notes skipped: {result.notes_skipped}")
    typer.echo(f"  Duration: {result.duration_ms}ms")

    if dry_run and result.previews:
        typer.echo(f"\n🔍 Dry-run mode - {len(result.previews)} notes would be created:")
        for preview in result.previews[:5]:  # Show first 5
            typer.echo(f"\n  📄 {preview['path']}")
            typer.echo(f"     {preview['content'][:200]}...")
        if len(result.previews) > 5:
            typer.echo(f"\n  ... and {len(result.previews) - 5} more")


@obsidian_app.command("config")
def obsidian_config(
    vault_path: Optional[str] = typer.Option(None, "--vault-path", "-v", help="Set vault path"),
    show: bool = typer.Option(False, "--show", help="Show current config"),
) -> None:
    """Configure Obsidian integration."""
    config_manager = ObsidianConfigManager()

    if show:
        typer.echo(config_manager.show())
    elif vault_path:
        config = config_manager.load()
        # Update vault path
        from src.domain.obsidian_models import ObsidianConfig

        new_config = ObsidianConfig(
            vault_path=Path(vault_path).expanduser().resolve(),
            default_segment=config.default_segment,
            min_priority=config.min_priority,
            note_folder=config.note_folder,
            auto_link=config.auto_link,
            date_format=config.date_format,
        )
        config_manager.save(new_config)
        typer.echo(f"✅ Vault path set to: {new_config.vault_path}")
        typer.echo("\nRun 'trifecta obsidian config --show' to see full config")
    else:
        typer.echo("Usage:")
        typer.echo("  trifecta obsidian config --vault-path <path>   Set vault path")
        typer.echo("  trifecta obsidian config --show               Show current config")
        raise typer.Exit(code=1)


@obsidian_app.command("validate")
def obsidian_validate() -> None:
    """Validate Obsidian vault configuration."""
    try:
        use_case = create_sync_use_case()
    except Exception as e:
        typer.echo(f"❌ Configuration error: {e}")
        raise typer.Exit(code=1)

    validation = use_case.validate_vault()

    if validation.valid:
        typer.echo("✅ Vault is valid and writable")
        typer.echo(f"   Findings folder: {validation.findings_dir}")
        typer.echo(f"   Existing notes: {validation.existing_notes}")
    else:
        typer.echo("❌ Vault validation failed")
        typer.echo(f"   Error: {validation.error}")
        raise typer.Exit(code=1)


def main() -> None:
    """Main entry point with custom error handling for invalid options."""
    try:
        # Use standalone_mode=False to capture exceptions
        # Note: typer.Exit is converted to a return value when standalone_mode=False
        exit_code = app(standalone_mode=False)

        # If app returned a non-zero exit code, exit with it
        if exit_code is not None and exit_code != 0:
            sys.exit(exit_code)

    except UsageError as e:
        # Handle Click UsageError (includes "No such option" errors)
        error_msg = str(e)

        # Check if this is an invalid option error
        if "no such option" in error_msg.lower():
            enhanced_msg = handle_invalid_option_error(error_msg, sys.argv)
            typer.echo(enhanced_msg, err=True)
            sys.exit(2)

        # For other usage errors, show the original message
        typer.echo(f"Error: {error_msg}", err=True)
        sys.exit(2)
    except click.exceptions.Exit as e:
        # Handle Click/typer.Exit exceptions (inherited from SystemExit)
        if e.exit_code != 0:
            sys.exit(e.exit_code)
    except SystemExit as e:
        # Handle normal exit codes
        if e.code is not None and e.code != 0:
            sys.exit(e.code)
    except Exception as e:
        # Handle unexpected errors with traceback for debugging
        typer.echo(f"Error: {e}", err=True)
        typer.echo(traceback.format_exc(), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
# Audit Trigger
# Audit Trigger Code
