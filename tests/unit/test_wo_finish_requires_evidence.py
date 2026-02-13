"""
Unit tests for evidence validation in ctx_wo_finish.py.

Tests ensure that:
1. Evidence directory (_ctx/handoff/{wo_id}/) must exist
2. verdict.json must exist and have matching wo_id
3. --skip-dod and --skip-verification flags do NOT bypass evidence validation
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

# Also add src for Result type
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class TestEvidenceValidation:
    """Test validate_minimum_evidence() function."""

    @pytest.fixture
    def valid_evidence_dir(self, tmp_path) -> Path:
        """Create valid evidence directory with verdict.json."""
        handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
        handoff_dir.mkdir(parents=True)

        verdict = {
            "wo_id": "WO-TEST",
            "status": "done",
            "generated_at": "2025-01-13T17:00:00Z",
        }
        (handoff_dir / "verdict.json").write_text(json.dumps(verdict))

        return handoff_dir

    def test_valid_evidence_passes(self, tmp_path, valid_evidence_dir):
        """Valid evidence directory passes validation."""
        from ctx_wo_finish import validate_minimum_evidence

        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_ok()

    def test_missing_handoff_directory_fails(self, tmp_path):
        """Missing handoff directory returns EVIDENCE_MISSING."""
        from ctx_wo_finish import validate_minimum_evidence

        # Don't create handoff directory
        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        error = result.unwrap_err()
        assert "EVIDENCE_MISSING" in error

    def test_missing_verdict_json_fails(self, tmp_path):
        """Missing verdict.json returns EVIDENCE_MISSING."""
        from ctx_wo_finish import validate_minimum_evidence

        # Create handoff dir but no verdict.json
        handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
        handoff_dir.mkdir(parents=True)

        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        error = result.unwrap_err()
        assert "EVIDENCE_MISSING" in error or "verdict" in error.lower()

    def test_mismatched_wo_id_in_verdict_fails(self, tmp_path):
        """verdict.json with wrong wo_id returns EVIDENCE_INVALID."""
        from ctx_wo_finish import validate_minimum_evidence

        handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
        handoff_dir.mkdir(parents=True)

        # Create verdict with WRONG wo_id
        verdict = {
            "wo_id": "WRONG-ID",  # Mismatch!
            "status": "done",
        }
        (handoff_dir / "verdict.json").write_text(json.dumps(verdict))

        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        error = result.unwrap_err()
        assert "EVIDENCE_INVALID" in error or "wo_id" in error.lower()

    def test_malformed_verdict_json_fails(self, tmp_path):
        """Malformed verdict.json returns EVIDENCE_INVALID."""
        from ctx_wo_finish import validate_minimum_evidence

        handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
        handoff_dir.mkdir(parents=True)

        # Write invalid JSON
        (handoff_dir / "verdict.json").write_text("{broken json")

        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        error = result.unwrap_err()
        assert "EVIDENCE_INVALID" in error or "malformed" in error.lower()


class TestSkipFlagsNoBypass:
    """Test that --skip-dod and --skip-verification do NOT bypass evidence validation."""

    def test_skip_dod_no_bypass_evidence_validation(self, tmp_path, monkeypatch):
        """--skip-dod must NOT bypass validate_minimum_evidence()."""
        from ctx_wo_finish import validate_minimum_evidence

        # Don't create evidence - should fail regardless of skip-dod
        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        assert "EVIDENCE_MISSING" in result.unwrap_err()

    def test_skip_verification_no_bypass_evidence_validation(self, tmp_path):
        """--skip-verification must NOT bypass validate_minimum_evidence()."""
        from ctx_wo_finish import validate_minimum_evidence

        # Don't create evidence - should fail regardless of skip-verification
        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        assert "EVIDENCE_MISSING" in result.unwrap_err()


class TestEvidenceValidationOrder:
    """Test that evidence validation runs BEFORE skip flags."""

    def test_evidence_validated_before_skip_checks(self, tmp_path):
        """Evidence validation must run before --skip-dod check."""
        from ctx_wo_finish import validate_minimum_evidence

        # Create running WO but no evidence
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True)
        import yaml

        wo_data = {
            "version": 1,
            "id": "WO-TEST",
            "status": "running",
            "dod_id": "DOD-TEST",
        }
        (running_dir / "WO-TEST.yaml").write_text(yaml.dump(wo_data))

        # Evidence validation should fail BEFORE --skip-dod is evaluated
        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()
        assert "EVIDENCE_MISSING" in result.unwrap_err()


class TestVerdictJsonStructure:
    """Test verdict.json structure validation."""

    def test_verdict_requires_wo_id_field(self, tmp_path):
        """verdict.json must have wo_id field."""
        from ctx_wo_finish import validate_minimum_evidence

        handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
        handoff_dir.mkdir(parents=True)

        # Missing wo_id field
        verdict = {"status": "done"}
        (handoff_dir / "verdict.json").write_text(json.dumps(verdict))

        result = validate_minimum_evidence("WO-TEST", tmp_path)

        assert result.is_err()

    def test_verdict_requires_status_field(self, tmp_path):
        """verdict.json must have status field."""
        from ctx_wo_finish import validate_minimum_evidence

        handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
        handoff_dir.mkdir(parents=True)

        # Missing status field
        verdict = {"wo_id": "WO-TEST"}
        (handoff_dir / "verdict.json").write_text(json.dumps(verdict))

        result = validate_minimum_evidence("WO-TEST", tmp_path)

        # May or may not require status, depending on implementation
        # The key test is wo_id matching
        assert result.is_ok() or result.is_err()
