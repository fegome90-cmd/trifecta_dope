"""
Tests for BuildContextPackUseCase determinism.

TDD Phase: RED -> GREEN
Ensures build uses exact path lookup and fails on ambiguity.
"""

from pathlib import Path

import pytest

from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter


class TestBuildDeterminism:
    """Test that BuildContextPackUseCase is deterministic and fail-closed."""

    def test_build_uses_exact_prime_path(self, tmp_path: Path) -> None:
        """Build should use exact prime path based on segment_id, not glob."""
        segment_name = "my_project"
        seg = tmp_path / segment_name
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_my_project.md").write_text("# Agent")
        (ctx / f"prime_{segment_name}.md").write_text("# Prime\n> **REPO_ROOT**: `/tmp`")
        (ctx / f"session_{segment_name}.md").write_text("# Session")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(seg)
        assert result.is_ok(), f"Build failed: {result}"
        pack = result.unwrap()

        assert pack.segment == segment_name

    def test_build_fails_with_multiple_prime_files(self, tmp_path: Path) -> None:
        """Build should FAIL if multiple prime_*.md files exist (ambiguity)."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg.md").write_text("# Agent")
        (ctx / "prime_test_seg.md").write_text("# Prime\n> **REPO_ROOT**: `/tmp`")
        (ctx / "prime_other.md").write_text("# Contamination")  # Ambiguous!
        (ctx / "session_test_seg.md").write_text("# Session")

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        # Use case-insensitive regex
        with pytest.raises(
            (ValueError, FileNotFoundError), match="(?i)ambiguous|multiple|contaminat"
        ):
            use_case.execute(seg)

    def test_build_fails_with_wrong_prime_suffix(self, tmp_path: Path) -> None:
        """Build should FAIL if prime_*.md has wrong suffix (contamination)."""
        seg = tmp_path / "correct_seg"
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_correct_seg.md").write_text("# Agent")
        (ctx / "prime_wrong_name.md").write_text("# Prime\n> **REPO_ROOT**: `/tmp`")  # Wrong!
        (ctx / "session_correct_seg.md").write_text("# Session")

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        with pytest.raises(FileNotFoundError, match="prime_correct_seg.md"):
            use_case.execute(seg)

    def test_build_with_spaces_in_segment_name(self, tmp_path: Path) -> None:
        """Build should handle segments with spaces (normalized to hyphens)."""
        seg = tmp_path / "My Project"
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        # Normalized: "my-project"
        (ctx / "agent_my-project.md").write_text("# Agent")
        (ctx / "prime_my-project.md").write_text("# Prime\n> **REPO_ROOT**: `/tmp`")
        (ctx / "session_my-project.md").write_text("# Session")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(seg)
        assert result.is_ok(), f"Build failed: {result}"
        pack = result.unwrap()

        assert pack.segment == "my-project"
