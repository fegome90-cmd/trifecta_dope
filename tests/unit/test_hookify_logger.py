"""Tests for HookifyEvidenceLogger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.infrastructure.hookify_logger import HookifyEvidenceLogger, HookifyViolation


@pytest.fixture
def temp_segment_root(tmp_path: Path) -> Path:
    """Create a temporary segment root for testing."""
    return tmp_path / "segment"


@pytest.fixture
def logger(temp_segment_root: Path) -> HookifyEvidenceLogger:
    """Create a logger instance for testing."""
    return HookifyEvidenceLogger(temp_segment_root)


class TestHookifyViolation:
    """Tests for HookifyViolation dataclass."""

    def test_create_violation(self):
        """Test creating a violation."""
        violation = HookifyViolation(
            id="test-1",
            timestamp="2026-01-03T12:00:00+00:00",
            rule_name="test-rule",
            pattern_matched="test-pattern",
            context={"file": "test.py", "line": "42"},
        )
        assert violation.id == "test-1"
        assert violation.status == "open"

    def test_to_dict(self):
        """Test converting violation to dict."""
        violation = HookifyViolation(
            id="test-1",
            timestamp="2026-01-03T12:00:00+00:00",
            rule_name="test-rule",
            pattern_matched="test-pattern",
            context={"file": "test.py"},
        )
        data = violation.to_dict()
        assert data["id"] == "test-1"
        assert data["status"] == "open"
        assert data["context"] == {"file": "test.py"}

    def test_from_dict_valid(self):
        """Test creating violation from valid dict."""
        data = {
            "id": "test-1",
            "timestamp": "2026-01-03T12:00:00+00:00",
            "rule_name": "test-rule",
            "pattern_matched": "test-pattern",
            "context": {"file": "test.py"},
        }
        violation = HookifyViolation.from_dict(data)
        assert violation.id == "test-1"
        assert violation.status == "open"

    def test_from_dict_missing_required_keys(self):
        """Test from_dict raises ValueError with missing keys."""
        data = {
            "id": "test-1",
            "timestamp": "2026-01-03T12:00:00+00:00",
            # Missing rule_name, pattern_matched, context
        }
        with pytest.raises(ValueError, match="Missing required keys"):
            HookifyViolation.from_dict(data)

    def test_from_dict_invalid_type(self):
        """Test from_dict raises TypeError with invalid type."""
        with pytest.raises(TypeError, match="Expected dict"):
            HookifyViolation.from_dict("not a dict")

    def test_from_dict_invalid_context(self):
        """Test from_dict raises TypeError with non-dict context."""
        data = {
            "id": "test-1",
            "timestamp": "2026-01-03T12:00:00+00:00",
            "rule_name": "test-rule",
            "pattern_matched": "test-pattern",
            "context": "not a dict",
        }
        with pytest.raises(TypeError, match="context must be a dict"):
            HookifyViolation.from_dict(data)


class TestHookifyEvidenceLogger:
    """Tests for HookifyEvidenceLogger."""

    def test_init_creates_evidence_file(self, temp_segment_root: Path):
        """Test initialization creates evidence directory."""
        logger = HookifyEvidenceLogger(temp_segment_root)
        assert logger.evidence_path.parent.exists()

    def test_log_violation(self, logger: HookifyEvidenceLogger):
        """Test logging a violation."""
        violation = logger.log_violation(
            rule_name="test-rule",
            pattern="test-pattern",
            context={"file": "test.py"},
        )
        assert violation.id.startswith("violation-")
        assert violation.rule_name == "test-rule"
        assert violation.status == "open"

    def test_log_violation_writes_to_file(self, logger: HookifyEvidenceLogger):
        """Test logging writes to evidence file."""
        logger.log_violation(
            rule_name="test-rule",
            pattern="test-pattern",
            context={"file": "test.py"},
        )
        assert logger.evidence_path.exists()

        with open(logger.evidence_path, encoding="utf-8") as f:
            content = f.read()
            assert "test-rule" in content

    def test_get_violations_empty(self, logger: HookifyEvidenceLogger):
        """Test getting violations when file doesn't exist."""
        violations = logger.get_violations()
        assert violations == []

    def test_get_violations_filters_by_status(self, logger: HookifyEvidenceLogger):
        """Test filtering violations by status."""
        logger.log_violation(
            rule_name="rule1",
            pattern="pattern1",
            context={},
        )
        logger.log_violation(
            rule_name="rule2",
            pattern="pattern2",
            context={},
        )
        v3 = logger.log_violation(
            rule_name="rule3",
            pattern="pattern3",
            context={},
        )
        logger.mark_resolved(v3.id)

        open_violations = logger.get_violations(status="open")
        assert len(open_violations) == 2

    def test_mark_resolved(self, logger: HookifyEvidenceLogger):
        """Test marking a violation as resolved."""
        violation = logger.log_violation(
            rule_name="test-rule",
            pattern="test-pattern",
            context={},
        )
        assert violation.status == "open"

        updated = logger.mark_resolved(violation.id)
        assert updated is not None
        assert updated.status == "resolved"
        assert updated.resolved_at is not None

    def test_mark_resolved_not_found(self, logger: HookifyEvidenceLogger):
        """Test marking non-existent violation returns None."""
        result = logger.mark_resolved("non-existent")
        assert result is None

    def test_mark_ignored(self, logger: HookifyEvidenceLogger):
        """Test marking a violation as ignored."""
        violation = logger.log_violation(
            rule_name="test-rule",
            pattern="test-pattern",
            context={},
        )
        assert violation.status == "open"

        updated = logger.mark_ignored(violation.id)
        assert updated is not None
        assert updated.status == "ignored"

    def test_clear_resolved(self, logger: HookifyEvidenceLogger):
        """Test clearing resolved violations."""
        v1 = logger.log_violation(
            rule_name="rule1",
            pattern="pattern1",
            context={},
        )
        v2 = logger.log_violation(
            rule_name="rule2",
            pattern="pattern2",
            context={},
        )
        logger.mark_resolved(v1.id)

        removed = logger.clear_resolved()
        assert removed == 1

        violations = logger.get_violations()
        assert len(violations) == 1
        assert violations[0].id == v2.id

    def test_stats(self, logger: HookifyEvidenceLogger):
        """Test getting violation statistics."""
        logger.log_violation(
            rule_name="rule1",
            pattern="pattern1",
            context={},
        )
        logger.log_violation(
            rule_name="rule1",
            pattern="pattern2",
            context={},
        )
        v3 = logger.log_violation(
            rule_name="rule2",
            pattern="pattern3",
            context={},
        )
        logger.mark_resolved(v3.id)

        stats = logger.stats()
        assert stats["total"] == 3
        assert stats["open"] == 2
        assert stats["resolved"] == 1
        assert stats["by_rule"]["rule1"] == 2
        assert stats["by_rule"]["rule2"] == 1

    def test_atomic_write(self, logger: HookifyEvidenceLogger):
        """Test that violations are written atomically."""
        logger.log_violation(
            rule_name="test-rule",
            pattern="test-pattern",
            context={},
        )

        # Verify file was written completely
        with open(logger.evidence_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.strip().split("\n")
            assert len(lines) == 1
            # Verify valid JSON
            data = json.loads(lines[0])
            assert data["rule_name"] == "test-rule"

    def test_handles_corrupted_lines(self, logger: HookifyEvidenceLogger):
        """Test that corrupted lines are skipped."""
        logger.log_violation(
            rule_name="rule1",
            pattern="pattern1",
            context={},
        )

        # Append corrupted line
        with open(logger.evidence_path, "a", encoding="utf-8") as f:
            f.write("invalid json\n")

        logger.log_violation(
            rule_name="rule2",
            pattern="pattern2",
            context={},
        )

        violations = logger.get_violations()
        # Should only return valid violations
        assert len(violations) == 2
        assert violations[0].rule_name == "rule1"
        assert violations[1].rule_name == "rule2"
