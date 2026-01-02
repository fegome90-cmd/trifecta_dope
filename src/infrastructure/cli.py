"""Trifecta CLI with T8 Telemetry."""

import json
import os
import time
from pathlib import Path
from typing import Literal, Optional, Tuple

import typer

from src.application.search_get_usecases import GetChunkUseCase, SearchUseCase
from src.application.telemetry_charts import generate_chart
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

app = typer.Typer(
    name="trifecta",
    help="Generate and manage Trifecta documentation packs for code segments.",
)

# AST/LSP Integration (Phase 2a/2b)
from src.infrastructure.cli_ast import ast_app

app.add_typer(ast_app, name="ast")

ctx_app = typer.Typer(help="Manage Trifecta Context Packs (ctx.search, ctx.get).")
session_app = typer.Typer(help="Session logging commands")
telemetry_app = typer.Typer(help="Telemetry analysis commands")

app.add_typer(ctx_app, name="ctx")
app.add_typer(session_app, name="session")
app.add_typer(telemetry_app, name="telemetry")

# AST/LSP Integration (Phase 2a)
from src.infrastructure.cli_ast import ast_app

app.add_typer(ast_app, name="ast")

# Legacy Burn-Down
legacy_app = typer.Typer(help="Legacy Burn-Down commands")
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
        validate_segment_fp,
    )

    segment_root = Path(segment)
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()

    # FP Gate: North Star Strict Validation
    match validate_segment_fp(segment_root):
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
            # 1. Fail-Closed: AGENTS.md Constitution
            match validate_agents_constitution(segment_root):
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
            legacy = detect_legacy_context_files(segment_root)
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

    _, file_system, _ = _get_dependencies(segment, telemetry)
    use_case = BuildContextPackUseCase(file_system, telemetry)
    segment_fs = segment_root.resolve()

    try:
        match use_case.execute(segment_fs):
            case Ok(pack):
                typer.echo(pack)
                telemetry.event(
                    "ctx.build",
                    {"segment": segment},
                    {"status": "ok"},
                    int((time.time() - start_time) * 1000),
                )
            case Err(errors):
                typer.echo("❌ Build Failed:")
                for err in errors:
                    typer.echo(f"   - {err}")
                telemetry.event(
                    "ctx.build",
                    {"segment": segment},
                    {"status": "build_error", "errors": len(errors)},
                    int((time.time() - start_time) * 1000),
                )
                telemetry.flush()
                raise typer.Exit(code=1)
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
        result = use_case.execute(Path(segment), task)

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
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    _, file_system, _ = _get_dependencies(segment, telemetry)

    try:
        typer.echo("🔄 Running build...")
        build_uc = BuildContextPackUseCase(file_system, telemetry)
        build_uc.execute(Path(segment).resolve())

        typer.echo("✅ Build complete. Validating...")
        validate_uc = ValidateContextPackUseCase(file_system, telemetry)
        result = validate_uc.execute(Path(segment).resolve())

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
            stub_result = stub_regen_uc.execute(Path(segment).resolve())

            if stub_result["stubs"]:
                typer.echo(f"   ✅ Regenerated: {', '.join(stub_result['stubs'])}")

            if stub_result["warnings"]:
                typer.echo("   ⚠️  Warnings:")
                for w in stub_result["warnings"]:
                    typer.echo(f"      - {w}")

            if not stub_result["regen_ok"]:
                typer.echo("   ⚠️  Stub regeneration had errors:")
                for e in stub_result["errors"]:
                    typer.echo(f"      - {e}")

        telemetry.event(
            "ctx.sync",
            {"segment": segment},
            {"status": "ok"},
            int((time.time() - start_time) * 1000),
        )

        if not result.passed:
            raise typer.Exit(code=1)

    # Type-based error classification (preferred - robust)
    except Exception as e:
        from src.application.exceptions import PrimeFileNotFoundError

        if isinstance(e, PrimeFileNotFoundError):
            # Prime file missing - emit SEGMENT_NOT_INITIALIZED Error Card
            from src.cli.error_cards import render_error_card

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
                {"segment": segment},
                {"status": "error", "error_code": "SEGMENT_NOT_INITIALIZED"},
                int((time.time() - start_time) * 1000),
            )
            typer.echo(error_card, err=True)
            raise typer.Exit(1)

        # Substring fallback for backward compatibility (deprecated)
        elif isinstance(e, FileNotFoundError) and "Expected prime file not found" in str(e):
            import sys
            from src.cli.error_cards import render_error_card
            from src.infrastructure.deprecations import maybe_emit_deprecated

            # Track deprecated usage (policy: off|warn|fail via env var)
            maybe_emit_deprecated("fallback_prime_missing_string_match", telemetry)

            # Emit deprecation warning for harness detection (legacy)
            print("TRIFECTA_DEPRECATED: fallback_prime_missing_string_match_used", file=sys.stderr)

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
                {"segment": segment},
                {"status": "error", "error_code": "SEGMENT_NOT_INITIALIZED"},
                int((time.time() - start_time) * 1000),
            )
            typer.echo(error_card, err=True)
            raise typer.Exit(1)

        # All other exceptions (fail-closed)
        else:
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
    segment: str = typer.Option(..., "--segment", "-s", help="Path to segment directory"),
    scope: str = typer.Option("Scope", "--scope", help="Short description of segment scope"),
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
    # FIXED: -s is now path to target directory (consistent with ctx sync/search/get)
    # Segment ID derived from directory name
    target_dir = Path(segment).resolve()

    template_renderer, _, _ = _get_dependencies(str(target_dir))

    if not target_dir.exists():
        target_dir.mkdir(parents=True)

    # Derive segment_id from directory name (same logic as use_cases.py)
    from src.domain.naming import normalize_segment_id

    segment_id = normalize_segment_id(target_dir.name)

    config = TrifectaConfig(
        segment=segment_id,
        scope=scope,
        repo_root=str(target_dir),
        last_verified=time.strftime("%Y-%m-%d"),
        default_profile="impl_patch",
    )

    files = {
        "skill.md": template_renderer.render_skill(config),
        "readme_tf.md": template_renderer.render_readme(config),
        f"_ctx/prime_{segment_id}.md": template_renderer.render_prime(config, []),
        f"_ctx/agent_{segment_id}.md": template_renderer.render_agent(config),
        f"_ctx/session_{segment_id}.md": template_renderer.render_session(config),
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
            files[f"_ctx/session_{segment_id}.md"]
            .split("## Quick Commands (CLI)")[1]
            .split("```")[1]
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


if __name__ == "__main__":
    app()
