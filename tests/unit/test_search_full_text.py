"""Tests for full-text search in ContextService."""

import json
from pathlib import Path

from src.application.context_service import ContextService
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


class TestSearchFullText:
    """Verify that search uses full chunk text instead of truncated preview."""

    def test_search_finds_keywords_in_full_text(self, tmp_path: Path) -> None:
        """Keywords beyond 200 chars should be found in full text search."""
        segment = tmp_path / "test_segment"
        segment.mkdir()

        padding = "x" * 250
        skill_content = (
            f"# Test Skill\n\n{padding}\n\npytest fixtures mocking are important for testing.\n"
        )
        (segment / "skill.md").write_text(skill_content)

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "prime_test_segment.md").write_text("# Prime\n\n")
        (ctx_dir / "agent_test_segment.md").write_text("# Agent\n\n")
        (ctx_dir / "session_test_segment.md").write_text("# Session\n\n")
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(_create_config(segment)) + "\n")

        fs = FileSystemAdapter()
        use_case = BuildContextPackUseCase(file_system=fs)
        result = use_case.execute(segment)
        assert isinstance(result, Ok), f"Build failed: {result}"

        service = ContextService(segment)
        search_result = service.search("pytest", k=5)

        assert len(search_result.hits) > 0, "Should find 'pytest' in full text"

    def test_search_finds_keywords_in_deep_content(self, tmp_path: Path) -> None:
        """Keywords deep in content should be found."""
        segment = tmp_path / "test_segment"
        segment.mkdir()

        padding = "x" * 500
        skill_content = f"# Test Skill\n\n{padding}\n\nmocking is a technique for unit tests.\n"
        (segment / "skill.md").write_text(skill_content)

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

        service = ContextService(segment)
        search_result = service.search("mocking", k=5)

        assert len(search_result.hits) > 0, "Should find 'mocking' deep in content"

    def test_search_preserves_preview_for_display(self, tmp_path: Path) -> None:
        """Search should return preview from index for display purposes."""
        segment = tmp_path / "test_segment"
        segment.mkdir()

        skill_content = "# Test Skill\n\n" + "x" * 600 + "\n\npytest fixtures.\n"
        (segment / "skill.md").write_text(skill_content)

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

        service = ContextService(segment)
        search_result = service.search("pytest", k=5)

        assert len(search_result.hits) > 0
        for hit in search_result.hits:
            assert len(hit.preview) <= 503, "Preview should be truncated (500 + '...')"
