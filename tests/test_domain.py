"""Tests for Domain Models."""
import pytest
from src.domain.models import TrifectaConfig, TrifectaPack, ValidationResult
from src.domain.constants import validate_profile, VALID_PROFILES


class TestTrifectaConfig:
    def test_valid_segment(self) -> None:
        config = TrifectaConfig(
            segment="eval-harness",
            scope="Evaluation harness",
            repo_root="/path/to/repo",
        )
        assert config.segment == "eval-harness"

    def test_segment_normalization(self) -> None:
        config = TrifectaConfig(
            segment="My_Segment",
            scope="Test",
            repo_root="/path",
        )
        assert config.segment == "my-segment"

    def test_invalid_segment_with_spaces(self) -> None:
        with pytest.raises(ValueError, match="no spaces"):
            TrifectaConfig(
                segment="my segment",
                scope="Test",
                repo_root="/path",
            )

    def test_empty_segment(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            TrifectaConfig(
                segment="",
                scope="Test",
                repo_root="/path",
            )


class TestTrifectaPack:
    def test_skill_line_count(self) -> None:
        config = TrifectaConfig(
            segment="test",
            scope="Test",
            repo_root="/path",
        )
        pack = TrifectaPack(
            config=config,
            skill_content="line1\nline2\nline3",
            prime_content="prime",
            agent_content="agent",
            session_content="session",
        )
        assert pack.skill_line_count == 3


class TestValidationResult:
    def test_passed_result(self) -> None:
        result = ValidationResult(passed=True)
        assert result.passed
        assert result.errors == []

    def test_failed_result(self) -> None:
        result = ValidationResult(
            passed=False,
            errors=["Missing skill.md"],
        )
        assert not result.passed
        assert len(result.errors) == 1


class TestValidateProfile:
    def test_valid_profile_returns_profile(self) -> None:
        for profile in VALID_PROFILES:
            result = validate_profile(profile)
            assert result == profile

    def test_invalid_profile_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid profile"):
            validate_profile("invalid_profile_name")

    def test_invalid_profile_error_message(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            validate_profile("bad_profile")
        error_msg = str(exc_info.value)
        assert "Invalid profile" in error_msg
        assert "bad_profile" in error_msg
        for valid_profile in VALID_PROFILES:
            assert valid_profile in error_msg
