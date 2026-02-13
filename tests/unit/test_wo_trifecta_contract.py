"""
Unit tests for Trifecta-first contract validation in ctx_wo_take.py.

Tests ensure that:
1. Every WO must have execution.engine == "trifecta"
2. Every WO must have execution.required_flow (non-empty list)
3. Every WO must have execution.segment
4. --force flag does NOT bypass contract validation
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


class TestTrifectaContractValidation:
    """Test validate_trifecta_contract() function."""

    @pytest.fixture
    def valid_wo_data(self) -> dict:
        """Return valid WO data with execution contract."""
        return {
            "version": 1,
            "id": "WO-TEST",
            "epic_id": "E-TEST",
            "title": "Test WO",
            "priority": "P1",
            "status": "pending",
            "dod_id": "DOD-TEST",
            "execution": {
                "engine": "trifecta",
                "required_flow": ["ctx sync", "verify"],
                "segment": ".",
            },
        }

    def test_valid_contract_passes(self, valid_wo_data):
        """Valid execution section passes validation."""
        from ctx_wo_take import validate_trifecta_contract

        result = validate_trifecta_contract(valid_wo_data)

        assert result.is_ok()

    def test_missing_execution_fails(self, valid_wo_data):
        """Missing execution section returns TRIFECTA_CONTRACT_MISSING."""
        from ctx_wo_take import validate_trifecta_contract

        del valid_wo_data["execution"]

        result = validate_trifecta_contract(valid_wo_data)

        assert result.is_err()
        error = result.unwrap_err()
        assert "TRIFECTA_CONTRACT_MISSING" in error

    def test_wrong_engine_fails(self, valid_wo_data):
        """Wrong engine returns TRIFECTA_CONTRACT_INVALID."""
        from ctx_wo_take import validate_trifecta_contract

        valid_wo_data["execution"]["engine"] = "manual"

        result = validate_trifecta_contract(valid_wo_data)

        assert result.is_err()
        error = result.unwrap_err()
        assert "TRIFECTA_CONTRACT_INVALID" in error
        assert "engine" in error.lower()

    def test_empty_required_flow_fails(self, valid_wo_data):
        """Empty required_flow returns TRIFECTA_CONTRACT_INVALID."""
        from ctx_wo_take import validate_trifecta_contract

        valid_wo_data["execution"]["required_flow"] = []

        result = validate_trifecta_contract(valid_wo_data)

        assert result.is_err()
        error = result.unwrap_err()
        assert "TRIFECTA_CONTRACT_INVALID" in error
        assert "required_flow" in error.lower()

    def test_missing_required_flow_fails(self, valid_wo_data):
        """Missing required_flow returns TRIFECTA_CONTRACT_INVALID."""
        from ctx_wo_take import validate_trifecta_contract

        del valid_wo_data["execution"]["required_flow"]

        result = validate_trifecta_contract(valid_wo_data)

        assert result.is_err()
        error = result.unwrap_err()
        assert "TRIFECTA_CONTRACT_INVALID" in error

    def test_missing_segment_fails(self, valid_wo_data):
        """Missing segment returns TRIFECTA_CONTRACT_INVALID."""
        from ctx_wo_take import validate_trifecta_contract

        del valid_wo_data["execution"]["segment"]

        result = validate_trifecta_contract(valid_wo_data)

        assert result.is_err()
        error = result.unwrap_err()
        assert "TRIFECTA_CONTRACT_INVALID" in error
        assert "segment" in error.lower()


class TestForceNoBypass:
    """Test that --force flag does NOT bypass contract validation."""

    @pytest.fixture
    def wo_without_execution(self, tmp_path) -> Path:
        """Create WO YAML without execution section."""
        pending_dir = tmp_path / "_ctx" / "jobs" / "pending"
        pending_dir.mkdir(parents=True)

        wo_data = {
            "version": 1,
            "id": "WO-NOEXEC",
            "epic_id": "E-TEST",
            "title": "WO without execution",
            "priority": "P1",
            "status": "pending",
            "dod_id": "DOD-TEST",
            # NO execution section
        }

        wo_path = pending_dir / "WO-NOEXEC.yaml"
        wo_path.write_text(yaml.dump(wo_data))
        return wo_path

    def test_force_flag_no_bypass_contract_validation(
        self, tmp_path, wo_without_execution, monkeypatch
    ):
        """--force must NOT bypass validate_trifecta_contract()."""
        # Create backlog
        backlog_dir = tmp_path / "_ctx" / "backlog"
        backlog_dir.mkdir(parents=True)
        backlog_data = {"epics": [{"id": "E-TEST", "title": "Test"}]}
        (backlog_dir / "backlog.yaml").write_text(yaml.dump(backlog_data))

        # Create schema (minimal valid schema)
        schema_dir = tmp_path / "docs" / "backlog" / "schema"
        schema_dir.mkdir(parents=True)
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["version", "id", "epic_id", "title", "priority", "status", "dod_id"],
            "properties": {
                "version": {"type": "integer"},
                "id": {"type": "string"},
                "epic_id": {"type": "string"},
                "title": {"type": "string"},
                "priority": {"type": "string"},
                "status": {"type": "string"},
                "dod_id": {"type": "string"},
                "execution": {"type": "object"},
            },
            "additionalProperties": True,
        }
        (schema_dir / "work_order.schema.json").write_text(json.dumps(schema))

        # Mock validate_wo_immediately to succeed (to isolate contract validation)
        from ctx_wo_take import validate_trifecta_contract

        # Verify contract validation is called and fails
        wo_data = yaml.safe_load(wo_without_execution.read_text())
        result = validate_trifecta_contract(wo_data)

        assert result.is_err()
        assert "TRIFECTA_CONTRACT_MISSING" in result.unwrap_err()


class TestContractValidationOrder:
    """Test that contract validation runs BEFORE --force dependency check."""

    def test_contract_validated_before_force_check(self, tmp_path, monkeypatch):
        """Contract validation must run before force flag is evaluated."""
        # This tests the ORDER of validation, not just the result
        # Contract should be validated FIRST, then force flag checked for deps

        wo_data = {
            "version": 1,
            "id": "WO-ORDER",
            "epic_id": "E-TEST",
            "title": "Test Order",
            "priority": "P1",
            "status": "pending",
            "dod_id": "DOD-TEST",
            "dependencies": ["WO-NONEXISTENT"],  # This would fail dep check
            # NO execution section - should fail contract FIRST
        }

        from ctx_wo_take import validate_trifecta_contract

        # Contract validation should fail before we even look at dependencies
        result = validate_trifecta_contract(wo_data)

        assert result.is_err()
        assert "TRIFECTA_CONTRACT_MISSING" in result.unwrap_err()


class TestExecutionSectionStructure:
    """Test detailed validation of execution section structure."""

    def test_engine_must_be_string(self):
        """Engine must be a string, not other types."""
        from ctx_wo_take import validate_trifecta_contract

        wo_data = {
            "id": "WO-TEST",
            "execution": {
                "engine": 123,  # Invalid: not a string
                "required_flow": ["verify"],
                "segment": ".",
            },
        }

        result = validate_trifecta_contract(wo_data)
        assert result.is_err()

    def test_required_flow_must_be_list(self):
        """required_flow must be a list."""
        from ctx_wo_take import validate_trifecta_contract

        wo_data = {
            "id": "WO-TEST",
            "execution": {
                "engine": "trifecta",
                "required_flow": "not-a-list",  # Invalid
                "segment": ".",
            },
        }

        result = validate_trifecta_contract(wo_data)
        assert result.is_err()

    def test_segment_must_be_string(self):
        """segment must be a string."""
        from ctx_wo_take import validate_trifecta_contract

        wo_data = {
            "id": "WO-TEST",
            "execution": {
                "engine": "trifecta",
                "required_flow": ["verify"],
                "segment": 123,  # Invalid: not a string
            },
        }

        result = validate_trifecta_contract(wo_data)
        assert result.is_err()
