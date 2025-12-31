"""
Tests for symmetric ambiguity and strict legacy enforcement in BuildContextPackUseCase.

TDD Phase: RED -> GREEN
Ensures strict 1:1 mapping for agent and session files, and fail-closed on legacy.
"""

from pathlib import Path
import pytest
from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter


class TestBuildSymmetricAmbiguity:
    """Test strict fail-closed logic for agent and session layers."""

    def test_build_fails_with_multiple_agent_files(self, tmp_path: Path) -> None:
        """Build should FAIL if multiple agent_*.md files exist."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "prime_test_seg.md").write_text("# Prime")
        # Ambiguous Agents
        (ctx / "agent_test_seg.md").write_text("# Agent 1")
        (ctx / "agent_other.md").write_text("# Agent 2")
        (ctx / "session_test_seg.md").write_text("# Session")

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        with pytest.raises(
            (ValueError, FileNotFoundError), match="(?i)ambiguous|multiple|contamination"
        ):
            use_case.execute(seg)

    def test_build_fails_with_multiple_session_files(self, tmp_path: Path) -> None:
        """Build should FAIL if multiple session_*.md files exist."""
        seg = tmp_path / "test_seg_s"
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "prime_test_seg_s.md").write_text("# Prime")
        (ctx / "agent_test_seg_s.md").write_text("# Agent")
        # Ambiguous Sessions
        (ctx / "session_test_seg_s.md").write_text("# Session 1")
        (ctx / "session_backup.md").write_text("# Session 2")

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        with pytest.raises(
            (ValueError, FileNotFoundError), match="(?i)ambiguous|multiple|contamination"
        ):
            use_case.execute(seg)

    def test_build_fails_with_contaminated_agent_suffix(self, tmp_path: Path) -> None:
        """Build should FAIL if ONLY 'agent_wrong.md' exists (contamination/mismatch)."""
        seg = tmp_path / "strict_seg"
        seg.mkdir()
        (seg / "skill.md").write_text("# Skill")
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "prime_strict_seg.md").write_text("# Prime")
        # Wrong suffix
        (ctx / "agent_wrong.md").write_text("# Agent")

        use_case = BuildContextPackUseCase(FileSystemAdapter())

        # Should fail either finding expected (FileNotFound) OR detecting contamination (ValueError)
        # We accept either as "Fail Closed"
        with pytest.raises((ValueError, FileNotFoundError)):
            use_case.execute(seg)
