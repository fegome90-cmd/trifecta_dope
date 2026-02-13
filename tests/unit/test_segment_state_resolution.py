from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.exceptions import InvalidConfigScopeError, InvalidSegmentPathError
from src.infrastructure.file_system import FileSystemAdapter
from src.infrastructure.segment_state import resolve_segment_state


def _write_config(segment_root: Path, *, segment: str, repo_root: str) -> None:
    ctx = segment_root / "_ctx"
    ctx.mkdir(parents=True, exist_ok=True)
    (ctx / "trifecta_config.json").write_text(
        json.dumps(
            {
                "segment": segment,
                "scope": "tests",
                "repo_root": repo_root,
                "default_profile": "impl_patch",
                "last_verified": "2026-02-11",
            }
        )
    )


def test_resolve_segment_state_dot_equals_abs_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    segment_root = tmp_path / "my_segment"
    segment_root.mkdir()
    _write_config(
        segment_root,
        segment="configured-segment",
        repo_root=str(segment_root),
    )

    monkeypatch.chdir(segment_root)
    fs = FileSystemAdapter()

    from_dot = resolve_segment_state(".", fs)
    from_abs = resolve_segment_state(str(segment_root), fs)

    assert from_dot.segment_root_resolved == from_abs.segment_root_resolved
    assert from_dot.segment_id == from_abs.segment_id
    assert from_dot.config_path_used == from_abs.config_path_used
    assert from_dot.segment_input_normalized == from_abs.segment_input_normalized


def test_resolve_segment_state_rejects_nonexistent_path(tmp_path: Path) -> None:
    fs = FileSystemAdapter()
    invalid_path = tmp_path / "does_not_exist"

    with pytest.raises(InvalidSegmentPathError):
        resolve_segment_state(str(invalid_path), fs)


def test_resolve_segment_state_rejects_invalid_config_scope(tmp_path: Path) -> None:
    segment_root = tmp_path / "scope_mismatch"
    segment_root.mkdir()
    _write_config(
        segment_root,
        segment="scope-mismatch",
        repo_root=str(tmp_path / "other_root"),
    )

    fs = FileSystemAdapter()

    with pytest.raises(InvalidConfigScopeError):
        resolve_segment_state(str(segment_root), fs)
