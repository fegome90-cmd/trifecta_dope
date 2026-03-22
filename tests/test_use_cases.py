"""Tests for Use Cases."""

import tempfile
from pathlib import Path


from src.domain.models import TrifectaConfig
from src.application.use_cases import (
    CreateTrifectaUseCase,
    MacroLoadUseCase,
    ValidateTrifectaUseCase,
)
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter


class TestCreateTrifectaUseCase:
    def test_create_trifecta_success(self) -> None:
        template_renderer = TemplateRenderer()
        file_system = FileSystemAdapter()
        use_case = CreateTrifectaUseCase(template_renderer, file_system)

        config = TrifectaConfig(
            segment="test-segment",
            scope="Test scope",
            repo_root="/tmp",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test-segment"
            pack = use_case.execute(config, target, [])

            assert pack.config.segment == "test-segment"
            assert (target / "skill.md").exists()
            assert (target / "_ctx" / "prime_test-segment.md").exists()
            assert (target / "_ctx" / "agent.md").exists()
            assert (target / "_ctx" / "session_test-segment.md").exists()


class TestValidateTrifectaUseCase:
    def test_validate_complete_trifecta(self) -> None:
        file_system = FileSystemAdapter()
        validate_use_case = ValidateTrifectaUseCase(file_system)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "valid-segment"
            ctx_dir = target / "_ctx"
            ctx_dir.mkdir(parents=True)
            (target / "skill.md").write_text("# Skill")
            (ctx_dir / "prime_valid-segment.md").write_text("# Prime")
            (ctx_dir / "agent_valid-segment.md").write_text("# Agent")
            (ctx_dir / "session_valid-segment.md").write_text("# Session")

            result = validate_use_case.execute(target)
            assert result.passed
            assert result.errors == []

    def test_validate_missing_skill(self) -> None:
        file_system = FileSystemAdapter()
        use_case = ValidateTrifectaUseCase(file_system)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "invalid-segment"
            target.mkdir(parents=True)

            result = use_case.execute(target)
            assert not result.passed
            assert "Missing: skill.md" in result.errors

    def test_validate_missing_ctx_dir(self) -> None:
        file_system = FileSystemAdapter()
        use_case = ValidateTrifectaUseCase(file_system)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "no-ctx"
            target.mkdir(parents=True)
            (target / "skill.md").write_text("# Skill")

            result = use_case.execute(target)
            assert not result.passed
            assert "Missing: _ctx/ directory" in result.errors

    def test_validate_accepts_canonical_agent_file_without_legacy_agent_md(self) -> None:
        file_system = FileSystemAdapter()
        use_case = ValidateTrifectaUseCase(file_system)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "canon-segment"
            ctx_dir = target / "_ctx"
            ctx_dir.mkdir(parents=True)
            (target / "skill.md").write_text("# Skill")
            (ctx_dir / "prime_canon-segment.md").write_text("# Prime")
            (ctx_dir / "agent_canon-segment.md").write_text("# Agent")

            result = use_case.execute(target)

            assert result.passed
            assert "Missing: _ctx/agent.md" not in result.errors


class TestMacroLoadUseCase:
    def test_fallback_load_prefers_canonical_agent_file_for_implementation_tasks(self) -> None:
        use_case = MacroLoadUseCase(file_system=FileSystemAdapter())

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "canon-segment"
            ctx_dir = target / "_ctx"
            ctx_dir.mkdir(parents=True)
            (target / "skill.md").write_text("# Skill Root")
            (ctx_dir / "agent_canon-segment.md").write_text("# Canon Agent")
            (ctx_dir / "agent.md").write_text("# Legacy Agent")

            output = use_case._fallback_load(target, "implement runtime fix")

            assert "## File: agent_canon-segment.md" in output
            assert "# Canon Agent" in output
            assert "# Legacy Agent" not in output
