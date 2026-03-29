"""Tests for preview length in context pack indexing."""

import json
from pathlib import Path

from src.application.use_cases import BuildContextPackUseCase
from src.domain.result import Ok
from src.infrastructure.file_system import FileSystemAdapter


def _create_config(segment_path: Path) -> dict:
    """Create valid trifecta_config.json data."""
    return {
        "segment": segment_path.name,
        "scope": f"Test segment {segment_path.name}",
        "repo_root": str(segment_path),
    }


class TestPreviewLength:
    """Verify that preview length is increased from 200 to 500 chars."""

    def test_preview_length_minimum_500_chars(self, tmp_path: Path) -> None:
        """Preview should be at least 500 chars for content > 500 chars."""
        segment = tmp_path / "test_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Test Skill\n\n" + "x" * 600 + "\n")
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "prime_test_segment.md").write_text("# Prime\n\n" + "y" * 600 + "\n")
        (ctx_dir / "agent_test_segment.md").write_text("# Agent\n\n" + "z" * 600 + "\n")
        (ctx_dir / "session_test_segment.md").write_text("# Session\n\n")
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(_create_config(segment)) + "\n")

        fs = FileSystemAdapter()
        use_case = BuildContextPackUseCase(file_system=fs)
        result = use_case.execute(segment)

        assert isinstance(result, Ok), f"Build failed: {result}"
        pack = result.value

        for entry in pack.index:
            if entry.token_est > 125:
                assert len(entry.preview) >= 500, (
                    f"Preview for {entry.id} is only {len(entry.preview)} chars, "
                    f"expected >= 500 chars"
                )

    def test_preview_uses_ellipsis_for_long_content(self, tmp_path: Path) -> None:
        """Preview should end with '...' for content > 500 chars."""
        segment = tmp_path / "test_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Test Skill\n\n" + "x" * 1000 + "\n")
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "prime_test_segment.md").write_text("# Prime\n\n")
        (ctx_dir / "agent_test_segment.md").write_text("# Agent\n\n")
        (ctx_dir / "session_test_segment.md").write_text("# Session\n\n")
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(_create_config(segment)) + "\n")

        fs = FileSystemAdapter()
        use_case = BuildContextPackUseCase(file_system=fs)
        result = use_case.execute(segment)

        assert isinstance(result, Ok)
        pack = result.value

        skill_entries = [e for e in pack.index if "skill" in e.id]
        assert len(skill_entries) > 0

        for entry in skill_entries:
            assert entry.preview.endswith("..."), f"Preview for {entry.id} doesn't end with '...'"

    def test_preview_no_ellipsis_for_short_content(self, tmp_path: Path) -> None:
        """Preview should NOT have '...' for content <= 500 chars."""
        segment = tmp_path / "test_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Short Skill\n\nShort content.\n")
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "prime_test_segment.md").write_text("# Prime\n\n")
        (ctx_dir / "agent_test_segment.md").write_text("# Agent\n\n")
        (ctx_dir / "session_test_segment.md").write_text("# Session\n\n")
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(_create_config(segment)) + "\n")

        fs = FileSystemAdapter()
        use_case = BuildContextPackUseCase(file_system=fs)
        result = use_case.execute(segment)

        assert isinstance(result, Ok)
        pack = result.value

        skill_entries = [e for e in pack.index if "skill" in e.id]
        assert len(skill_entries) > 0

        for entry in skill_entries:
            assert not entry.preview.endswith("..."), (
                f"Preview for {entry.id} incorrectly ends with '...'"
            )
