"""
Tests for AGENTS.md Constitution Gate (Phase 1).

Contract:
1. AGENTS.md must exist in the segment root.
2. AGENTS.md must not be empty.
3. Returns Result[ValidationResult, list[str]].
"""

from pathlib import Path
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

    def test_read_error_returns_err(self, tmp_path: Path, monkeypatch) -> None:
        """Read failure (permission/etc) should return deterministic Err."""
        # Use a real path so validate_agents_constitution works until read_text
        seg = tmp_path / "test_seg_read_err"
        seg.mkdir()

        # AGENTS.md exists (check 1 passes)
        agents_path = seg / "AGENTS.md"
        agents_path.write_text("ok")

        # Mock read_text to raise OSError, requiring compatible signature (*args, **kwargs)
        # We target Path.read_text directly or the instance method if possible.
        # Patching Path.read_text is safest to catch the call.
        def mock_read_text(self, *args, **kwargs):
            if str(self).endswith("AGENTS.md"):
                raise OSError("Simulated Permission Denied")
            return "ok"  # fallback if needed, though mostly unused here

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        # Act
        result = validate_agents_constitution(seg)

        # Assert
        assert result.is_err()
        # Should be deterministic message, NOT containing the exception details
        assert result.unwrap_err() == ["Failed Constitution: AGENTS.md cannot be read"]
