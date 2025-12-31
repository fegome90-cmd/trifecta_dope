"""
Tests for AGENTS.md Constitution Gate (Phase 1).

Contract:
1. AGENTS.md must exist in the segment root.
2. AGENTS.md must not be empty.
3. Returns Result[ValidationResult, list[str]].
"""

from pathlib import Path
import pytest
from src.domain.result import Ok, Err
from src.infrastructure.validators import validate_agents_constitution


class TestAgentsConstitutionGate:
    """Test strict AGENTS.md validation."""

    def test_missing_agents_md_is_error(self, tmp_path: Path) -> None:
        """Missing AGENTS.md should return Err."""
        seg = tmp_path / "test_seg"
        seg.mkdir()

        # Valid structure otherwise
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg.md").touch()
        (ctx / "prime_test_seg.md").touch()
        (ctx / "session_test_seg.md").touch()

        # Act
        result = validate_agents_constitution(seg)

        # Assert
        assert result.is_err(), "Should fail if AGENTS.md is missing"
        errors = result.unwrap_err()
        assert any("missing AGENTS.md" in err for err in errors)

    def test_empty_agents_md_is_error(self, tmp_path: Path) -> None:
        """Empty AGENTS.md should return Err."""
        seg = tmp_path / "test_seg"
        seg.mkdir()

        # Create empty AGENTS.md
        (seg / "AGENTS.md").touch()

        # Act
        result = validate_agents_constitution(seg)

        # Assert
        assert result.is_err(), "Should fail if AGENTS.md is empty"
        errors = result.unwrap_err()
        assert any("empty" in err.lower() for err in errors)

    def test_valid_agents_md_passes(self, tmp_path: Path) -> None:
        """Valid AGENTS.md should return Ok."""
        seg = tmp_path / "test_seg"
        seg.mkdir()

        # Create valid AGENTS.md
        (seg / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")

        # Act
        result = validate_agents_constitution(seg)

        # Assert
        assert result.is_ok(), f"Should pass with valid AGENTS.md, got {result}"
