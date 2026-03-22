"""
CLI renderers for repository commands.

This module provides unified rendering functions for repository CLI output,
supporting both JSON and text formats.
"""

import json
from typing import TYPE_CHECKING, Any

import typer

if TYPE_CHECKING:
    from src.application.repo_use_case import RepoEntry


def render_repo_list(
    repos: list["RepoEntry"],
    json_output: bool,
    *,
    legacy_mode: bool = False,
) -> None:
    """
    Render repository list output.

    Args:
        repos: List of repository entries to render.
        json_output: If True, output as JSON; otherwise as text.
        legacy_mode: If True, use legacy format (array without wrapper, no slug).
                     Used for backward compatibility with deprecated alias.
    """
    if json_output:
        if legacy_mode:
            # Legacy format: plain array without slug
            output: Any = [{"repo_id": r.repo_id, "path": r.path} for r in repos]
        else:
            # Modern format: wrapped object with slug
            output = {
                "repos": [
                    {"repo_id": r.repo_id, "path": r.path, "slug": r.slug} for r in repos
                ]
            }
        typer.echo(json.dumps(output, indent=2))
    else:
        if not repos:
            typer.echo("No registered repositories")
        else:
            if legacy_mode:
                # Legacy format: simple list
                for repo in repos:
                    typer.echo(f"{repo.repo_id}: {repo.path}")
            else:
                # Modern format: header with count and slug
                typer.echo(f"Registered Repositories ({len(repos)}):")
                for repo in repos:
                    typer.echo(f"  - {repo.slug}: {repo.repo_id}")


def render_repo_register(
    entry: "RepoEntry",
    json_output: bool,
    *,
    legacy_mode: bool = False,
) -> None:
    """
    Render repository registration output.

    Args:
        entry: Repository entry that was registered.
        json_output: If True, output as JSON; otherwise as text.
        legacy_mode: If True, use legacy format (no slug/fingerprint).
    """
    if json_output:
        if legacy_mode:
            output = {"repo_id": entry.repo_id, "path": entry.path}
        else:
            output = {
                "repo_id": entry.repo_id,
                "path": entry.path,
                "slug": entry.slug,
                "fingerprint": entry.fingerprint,
            }
        typer.echo(json.dumps(output, indent=2))
    else:
        if legacy_mode:
            typer.echo(f"Registered: {entry.repo_id}")
        else:
            typer.echo(f"Registered: {entry.slug}")
            typer.echo(f"  ID: {entry.repo_id}")
            typer.echo(f"  Path: {entry.path}")


def render_repo_show(
    entry: "RepoEntry",
    json_output: bool,
    *,
    legacy_mode: bool = False,
) -> None:
    """
    Render repository show output.

    Args:
        entry: Repository entry to show.
        json_output: If True, output as JSON; otherwise as text.
        legacy_mode: If True, use legacy format (no fingerprint).
    """
    if json_output:
        if legacy_mode:
            output = {"repo_id": entry.repo_id, "path": entry.path, "slug": entry.slug}
        else:
            output = {
                "repo_id": entry.repo_id,
                "path": entry.path,
                "slug": entry.slug,
                "fingerprint": entry.fingerprint,
            }
        typer.echo(json.dumps(output, indent=2))
    else:
        if legacy_mode:
            typer.echo(f"Repository: {entry.repo_id}")
            typer.echo(f"  Path: {entry.path}")
            typer.echo(f"  Slug: {entry.slug}")
        else:
            typer.echo(f"Repository: {entry.slug}")
            typer.echo(f"  ID: {entry.repo_id}")
            typer.echo(f"  Path: {entry.path}")
            typer.echo(f"  Fingerprint: {entry.fingerprint}")
