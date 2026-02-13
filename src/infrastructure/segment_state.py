"""Segment state resolution for CLI commands (SSOT for build/sync preconditions)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.application.exceptions import InvalidConfigScopeError, InvalidSegmentPathError
from src.domain.naming import normalize_segment_id
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

    config_path = resolved_root / "_ctx" / "trifecta_config.json"
    config = file_system.load_trifecta_config(resolved_root)

    if config is not None:
        config_root = Path(config.repo_root).expanduser().resolve()
        if config_root != resolved_root:
            raise InvalidConfigScopeError(
                config_repo_root=config_root,
                resolved_segment_root=resolved_root,
            )
        segment_id = config.segment_id
        source = "config"
        config_path_used: Path | None = config_path
    else:
        segment_id = normalize_segment_id(resolved_root.name)
        source = "dirname"
        config_path_used = None

    ctx_dir = resolved_root / "_ctx"
    expected = (
        ctx_dir / f"agent_{segment_id}.md",
        ctx_dir / f"prime_{segment_id}.md",
        ctx_dir / f"session_{segment_id}.md",
    )

    return SegmentState(
        segment_input=segment_input,
        segment_input_normalized=str(resolved_root),
        segment_root_resolved=resolved_root,
        segment_id=segment_id,
        source_of_truth=source,
        config_path_used=config_path_used,
        expected_files=expected,
    )
