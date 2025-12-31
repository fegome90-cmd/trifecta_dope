"""Tests for strict fail-closed behavior on corrupt config."""

from pathlib import Path
from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter


def test_build_fails_closed_on_corrupt_config(tmp_path: Path) -> None:
    """Should return Err when trifecta_config.json is corrupt."""
    # Setup corrupted segment
    seg = tmp_path / "corrupt_seg"
    seg.mkdir()
    (seg / "skill.md").touch()
    ctx = seg / "_ctx"
    ctx.mkdir()
    (ctx / "trifecta_config.json").write_text("{imvalid_json: true,")

    # Use Case
    fs = FileSystemAdapter()
    uc = BuildContextPackUseCase(fs)

    # Act
    # Execute should NOT raise exception, but return Err
    result = uc.execute(seg)

    # Assert
    assert result.is_err()
    assert result.unwrap_err() == ["Failed Constitution: trifecta_config.json is invalid"]
