"""Tests for Use Cases."""
import tempfile
from pathlib import Path

import pytest

from src.domain.models import TrifectaConfig
from src.application.use_cases import (
    CreateTrifectaUseCase,
    ValidateTrifectaUseCase,
)
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter


class TestCreateTrifectaUseCase:
    def test_create_trifecta_success(self):
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
    def test_validate_complete_trifecta(self):
        template_renderer = TemplateRenderer()
        file_system = FileSystemAdapter()
        create_use_case = CreateTrifectaUseCase(template_renderer, file_system)
        validate_use_case = ValidateTrifectaUseCase(file_system)

        config = TrifectaConfig(
            segment="valid-segment",
            scope="Valid scope",
            repo_root="/tmp",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "valid-segment"
            create_use_case.execute(config, target, [])

            result = validate_use_case.execute(target)
            assert result.passed
            assert result.errors == []

    def test_validate_missing_skill(self):
        file_system = FileSystemAdapter()
        use_case = ValidateTrifectaUseCase(file_system)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "invalid-segment"
            target.mkdir(parents=True)

            result = use_case.execute(target)
            assert not result.passed
            assert "Missing: skill.md" in result.errors

    def test_validate_missing_ctx_dir(self):
        file_system = FileSystemAdapter()
        use_case = ValidateTrifectaUseCase(file_system)

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "no-ctx"
            target.mkdir(parents=True)
            (target / "skill.md").write_text("# Skill")

            result = use_case.execute(target)
            assert not result.passed
            assert "Missing: _ctx/ directory" in result.errors
