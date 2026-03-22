"""CLI commands for skill metadata and alias extraction.

This module provides:
- extract-keywords: Generate aliases.generated.yaml from skill metadata

Usage:
    trifecta skill extract-keywords --segment <path>
    trifecta skill extract-keywords --segment <path> --stdout
    trifecta skill extract-keywords --segment <path> --dry-run
    trifecta skill extract-keywords --segment <path> --check
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

from src.application.keyword_extractor import (
    GeneratedAliasMap,
    KeywordExtractor,
)
from src.infrastructure.aliases_fs import (
    GENERATED_ALIASES_FILENAME,
    GeneratedAliasWriter,
    load_aliases_yaml,
    load_skills_manifest,
)


def _print_metrics(
    skills_count: int,
    extracted_count: int,
    raw_tokens: int,
    aliases_count: int,
    capped_aliases: int,
    output_path: Path,
) -> None:
    """Print extraction metrics to stderr."""
    typer.echo("=== Keyword Extraction Report ===", err=True)
    typer.echo(f"Skills processed: {skills_count}", err=True)
    typer.echo(f"Skills with keywords: {extracted_count}", err=True)
    typer.echo(f"Raw tokens extracted: {raw_tokens}", err=True)
    typer.echo(f"Aliases generated: {aliases_count}", err=True)
    if capped_aliases > 0:
        typer.echo(f"Aliases capped (>8 skills): {capped_aliases}", err=True)
    typer.echo(f"Output path: {output_path}", err=True)


def run_extract_keywords(
    segment: str,
    output: Optional[str],
    min_frequency: int,
    max_skills_per_alias: int,
    stdout: bool,
    dry_run: bool,
    check: bool,
) -> None:
    """Run the extract-keywords command.

    This is the core implementation called by the CLI command.

    Args:
        segment: Target segment path.
        output: Custom output path (optional).
        min_frequency: Minimum frequency for a keyword.
        max_skills_per_alias: Maximum skills per alias.
        stdout: Print to stdout instead of file.
        dry_run: Don't persist changes.
        check: Fail if output differs from existing.
    """
    segment_path = Path(segment).expanduser().resolve()

    if not segment_path.exists():
        typer.echo(f"Error: Segment path does not exist: {segment_path}", err=True)
        raise typer.Exit(code=1)

    # Determine output path
    if output:
        output_path = Path(output).expanduser().resolve()
    else:
        output_path = segment_path / "_ctx" / GENERATED_ALIASES_FILENAME

    # Load skills from manifest
    skills = load_skills_manifest(segment_path)

    # Initialize metrics
    extracted_count = 0
    raw_tokens = 0
    capped_count = 0

    if not skills:
        typer.echo("Warning: No skills found in manifest", err=True)
        # Create empty output
        alias_map = GeneratedAliasMap(schema_version=1, aliases={})
    else:
        # Extract keywords
        extractor = KeywordExtractor(
            min_frequency=min_frequency,
            max_skills_per_alias=max_skills_per_alias,
        )

        extracted = extractor.extract_from_skills(skills)
        extracted_count = len(extracted)
        alias_map = extractor.build_alias_map(extracted)

        # Calculate metrics
        raw_tokens = sum(len(e.keywords) for e in extracted)
        capped_count = sum(
            1 for skills_list in alias_map.aliases.values()
            if len(skills_list) >= max_skills_per_alias
        )

    # Handle --check flag
    if check:
        if not output_path.exists():
            typer.echo(f"Error: Output file does not exist: {output_path}", err=True)
            typer.echo("Run without --check to create the file first.", err=True)
            raise typer.Exit(code=1)

        # Load existing and compare
        existing = load_aliases_yaml(output_path)
        if existing != alias_map.aliases:
            typer.echo("Error: Generated aliases differ from existing file", err=True)
            typer.echo("Run without --check to update the file.", err=True)
            raise typer.Exit(code=1)

        typer.echo("OK: Generated aliases match existing file", err=True)
        return

    # Handle --stdout flag
    if stdout:
        data = {"schema_version": alias_map.schema_version, "aliases": alias_map.aliases}
        yaml.dump(data, sys.stdout, default_flow_style=False, sort_keys=True, allow_unicode=True)
        return

    # Handle --dry-run flag
    if dry_run:
        typer.echo(f"Dry run: Would write to {output_path}", err=True)
        _print_metrics(
            skills_count=len(skills),
            extracted_count=extracted_count,
            raw_tokens=raw_tokens,
            aliases_count=len(alias_map.aliases),
            capped_aliases=capped_count,
            output_path=output_path,
        )
        return

    # Write the file
    writer = GeneratedAliasWriter(segment_path=segment_path, output_path=output_path)
    writer.write(alias_map.aliases)

    # Print metrics
    _print_metrics(
        skills_count=len(skills),
        extracted_count=extracted_count,
        raw_tokens=raw_tokens,
        aliases_count=len(alias_map.aliases),
        capped_aliases=capped_count,
        output_path=output_path,
    )

    typer.echo(f"Successfully generated: {output_path}")


# Create a standalone skills_app for testing
# (The main CLI uses the skill_app from cli.py)
skills_app = typer.Typer(
    help="Skill metadata and keyword extraction commands.",
    rich_markup_mode="rich",
)


@skills_app.command("extract-keywords")
def extract_keywords_standalone(
    segment: str = typer.Option(..., "--segment", "-s", help="Target segment path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output path"),
    min_frequency: int = typer.Option(2, "--min-frequency", "-f", help="Minimum frequency"),
    max_skills_per_alias: int = typer.Option(8, "--max-skills-per-alias", "-m", help="Max skills per alias"),
    stdout: bool = typer.Option(False, "--stdout", help="Print to stdout"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't persist"),
    check: bool = typer.Option(False, "--check", help="Fail if differs"),
) -> None:
    """Extract keywords from skill metadata and generate aliases (standalone)."""
    run_extract_keywords(
        segment=segment,
        output=output,
        min_frequency=min_frequency,
        max_skills_per_alias=max_skills_per_alias,
        stdout=stdout,
        dry_run=dry_run,
        check=check,
    )
