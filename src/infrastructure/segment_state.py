"""Segment state resolution for CLI commands (SSOT for build/sync preconditions)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.application.exceptions import InvalidSegmentPathError
from src.domain.segment_resolver import resolve_segment_ref
from src.infrastructure.file_system import FileSystemAdapter


@dataclass(frozen=True)
class SegmentState:
    """Resolved and normalized segment state used by command preconditions."""

    segment_input: str
    segment_input_normalized: str
    segment_root_resolved: Path
    segment_id: str
    source_of_truth: str
    config_path_used: Path | None
    expected_files: tuple[Path, Path, Path]


LEGACY_SINGLETONS = ("agent.md", "prime.md", "session.md")
CANONICAL_PREFIXES = ("agent", "prime", "session")


def _raise_canon_error(code: str) -> None:
    raise ValueError(code)


def _suffixes_for(ctx_dir: Path, prefix: str) -> set[str]:
    suffixes: set[str] = set()
    for path in ctx_dir.glob(f"{prefix}_*.md"):
        suffix = path.stem[len(prefix) + 1 :]
        if suffix:
            suffixes.add(suffix)
    return suffixes


def _legacy_singletons_present(ctx_dir: Path) -> list[str]:
    return [name for name in LEGACY_SINGLETONS if (ctx_dir / name).exists()]


def _other_canonical_family_paths(ctx_dir: Path, canonical_suffix: str) -> list[Path]:
    others: list[Path] = []
    for prefix in CANONICAL_PREFIXES:
        for path in ctx_dir.glob(f"{prefix}_*.md"):
            suffix = path.stem[len(prefix) + 1 :]
            if suffix != canonical_suffix:
                others.append(path)
    return others


def _files_for_suffix(ctx_dir: Path, suffix: str) -> tuple[Path, Path, Path]:
    return tuple(ctx_dir / f"{prefix}_{suffix}.md" for prefix in CANONICAL_PREFIXES)  # type: ignore[return-value]


def _suffix_presence(ctx_dir: Path, suffixes: Iterable[str]) -> tuple[set[str], set[str]]:
    complete: set[str] = set()
    partial: set[str] = set()
    for suffix in suffixes:
        files = _files_for_suffix(ctx_dir, suffix)
        present_count = sum(path.exists() for path in files)
        if present_count == len(files):
            complete.add(suffix)
        elif present_count > 0:
            partial.add(suffix)
    return complete, partial


def resolve_segment_state(segment_input: str, file_system: FileSystemAdapter) -> SegmentState:
    """Resolve segment root and derive a deterministic segment identity.

    Rules:
    - Resolve input using expanduser() + resolve()
    - Require existing directory
    - Use _ctx/trifecta_config.json at resolved root (non-recursive) when present
    - Validate config scope against resolved root
    - Fallback to normalized directory name when config is absent
    """
    raw = Path(segment_input).expanduser()
    resolved_root = raw.resolve()

    if not resolved_root.exists() or not resolved_root.is_dir():
        raise InvalidSegmentPathError(segment_input=segment_input, resolved_path=resolved_root)

    ctx_dir = resolved_root / "_ctx"
    config_path = ctx_dir / "trifecta_config.json"
    config = file_system.load_trifecta_config(resolved_root)

    config_scope_mismatch = False
    if config is not None:
        config_root = Path(config.repo_root).expanduser().resolve()
        config_scope_mismatch = config_root != resolved_root

    if not ctx_dir.exists():
        _raise_canon_error("SEGMENT_CANON_MISSING")

    legacy_singletons = _legacy_singletons_present(ctx_dir)
    suffixes = set().union(*(_suffixes_for(ctx_dir, prefix) for prefix in CANONICAL_PREFIXES))
    complete_suffixes, partial_suffixes = _suffix_presence(ctx_dir, suffixes)

    if len(complete_suffixes) > 1:
        _raise_canon_error("SEGMENT_CANON_AMBIGUOUS")

    if len(complete_suffixes) == 0:
        if len(partial_suffixes) == 1:
            _raise_canon_error("SEGMENT_CANON_INCOMPLETE")
        if len(partial_suffixes) > 1:
            _raise_canon_error("SEGMENT_CANON_AMBIGUOUS")
        _raise_canon_error("SEGMENT_CANON_MISSING")

    segment_id = next(iter(complete_suffixes))

    if _other_canonical_family_paths(ctx_dir, segment_id):
        _raise_canon_error("SEGMENT_CANON_CONTAMINATED")

    if legacy_singletons:
        _raise_canon_error("SEGMENT_CANON_CONTAMINATED")

    if config is not None and (config_scope_mismatch or config.segment_id != segment_id):
        _raise_canon_error("SEGMENT_CANON_CONTRADICTED_BY_LOCAL_CONFIG")

    source = "tracked"
    config_path_used: Path | None = config_path if config is not None else None
    expected = _files_for_suffix(ctx_dir, segment_id)

    return SegmentState(
        segment_input=segment_input,
        segment_input_normalized=str(resolved_root),
        segment_root_resolved=resolved_root,
        segment_id=segment_id,
        source_of_truth=source,
        config_path_used=config_path_used,
        expected_files=expected,
    )
