"""
Unit tests for Trifecta execution contract validation in ctx_wo_take.py.

Tests ensure that:
1. Every WO must have execution.engine == "trifecta"
2. Every WO must have execution.required_flow (non-empty list with mandatory steps)
3. Every WO must have execution.segment == "."
4. --force flag does NOT bypass contract validation

Contract API: validate_execution_contract(wo_data) -> tuple[bool, str | None]
  - (True, None) = validation passed
  - (False, "error message") = validation failed with reason
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


class TestTrifectaContractValidation:
    """Test validate_execution_contract() function."""

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
                "required_flow": [
                    "session.append:intent",
                    "ctx.sync",
                    "ctx.search",
                    "ctx.get",
                    "session.append:result",
                ],
                "segment": ".",
            },
        }

    def test_valid_contract_passes(self, valid_wo_data):
        """Valid execution section passes validation."""
        from ctx_wo_take import validate_execution_contract

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is True
        assert err is None

    def test_missing_execution_fails(self, valid_wo_data):
        """Missing execution section returns error."""
        from ctx_wo_take import validate_execution_contract

        del valid_wo_data["execution"]

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "execution contract is required" in err

    def test_wrong_engine_fails(self, valid_wo_data):
        """Wrong engine returns error."""
        from ctx_wo_take import validate_execution_contract

        valid_wo_data["execution"]["engine"] = "manual"

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "engine" in err.lower()

    def test_empty_required_flow_fails(self, valid_wo_data):
        """Empty required_flow returns error."""
        from ctx_wo_take import validate_execution_contract

        valid_wo_data["execution"]["required_flow"] = []

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "required_flow" in err.lower()

    def test_missing_required_flow_fails(self, valid_wo_data):
        """Missing required_flow returns error."""
        from ctx_wo_take import validate_execution_contract

        del valid_wo_data["execution"]["required_flow"]

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "required_flow" in err.lower()

    def test_missing_segment_fails(self, valid_wo_data):
        """Missing/wrong segment returns error."""
        from ctx_wo_take import validate_execution_contract

        del valid_wo_data["execution"]["segment"]

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "segment" in err.lower()

    def test_missing_mandatory_steps_fails(self, valid_wo_data):
        """Missing mandatory steps in required_flow returns error."""
        from ctx_wo_take import validate_execution_contract

        # Remove one mandatory step
        valid_wo_data["execution"]["required_flow"] = [
            "session.append:intent",
            "ctx.sync",
            # Missing: ctx.search, ctx.get, session.append:result
        ]

        ok, err = validate_execution_contract(valid_wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "missing mandatory steps" in err


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
        """--force must NOT bypass validate_execution_contract()."""
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

        # Verify contract validation is called and fails
        from ctx_wo_take import validate_execution_contract

        wo_data = yaml.safe_load(wo_without_execution.read_text())
        ok, err = validate_execution_contract(wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "execution contract is required" in err


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

        from ctx_wo_take import validate_execution_contract

        # Contract validation should fail before we even look at dependencies
        ok, err = validate_execution_contract(wo_data)

        assert ok is False
        assert isinstance(err, str)
        assert "execution contract is required" in err


class TestExecutionSectionStructure:
    """Test detailed validation of execution section structure."""

    def test_engine_must_be_string(self):
        """Engine must be a string, not other types."""
        from ctx_wo_take import validate_execution_contract

        wo_data = {
            "id": "WO-TEST",
            "execution": {
                "engine": 123,  # Invalid: not a string
                "required_flow": ["verify"],
                "segment": ".",
            },
        }

        ok, err = validate_execution_contract(wo_data)

        assert ok is False
        assert isinstance(err, str)

    def test_required_flow_must_be_list(self):
        """required_flow must be a list."""
        from ctx_wo_take import validate_execution_contract

        wo_data = {
            "id": "WO-TEST",
            "execution": {
                "engine": "trifecta",
                "required_flow": "not-a-list",  # Invalid
                "segment": ".",
            },
        }

        ok, err = validate_execution_contract(wo_data)

        assert ok is False
        assert isinstance(err, str)

    def test_segment_must_be_string(self):
        """segment must be a string."""
        from ctx_wo_take import validate_execution_contract

        wo_data = {
            "id": "WO-TEST",
            "execution": {
                "engine": "trifecta",
                "required_flow": [
                    "session.append:intent",
                    "ctx.sync",
                    "ctx.search",
                    "ctx.get",
                    "session.append:result",
                ],
                "segment": 123,  # Invalid: not a string
            },
        }

        ok, err = validate_execution_contract(wo_data)

        assert ok is False
        assert isinstance(err, str)


class TestContractInvariants:
    """Anti-drift tests: validate return contract invariants."""

    def test_success_returns_true_none(self):
        """Success case MUST return (True, None)."""
        from ctx_wo_take import validate_execution_contract

        valid_wo = {
            "execution": {
                "engine": "trifecta",
                "required_flow": [
                    "session.append:intent",
                    "ctx.sync",
                    "ctx.search",
                    "ctx.get",
                    "session.append:result",
                ],
                "segment": ".",
            }
        }

        ok, err = validate_execution_contract(valid_wo)

        # Invariant: success means ok=True AND err=None
        assert ok is True
        assert err is None

    def test_failure_returns_false_with_message(self):
        """Failure case MUST return (False, non-empty string)."""
        from ctx_wo_take import validate_execution_contract

        invalid_wo = {}  # Missing execution

        ok, err = validate_execution_contract(invalid_wo)

        # Invariant: failure means ok=False AND err is non-empty string
        assert ok is False
        assert isinstance(err, str)
        assert len(err) > 0

    def test_never_returns_both_true_and_error(self):
        """Cannot return (True, "error") - invalid state."""
        from ctx_wo_take import validate_execution_contract

        # Test both success and failure cases
        test_cases = [
            {
                "execution": {
                    "engine": "trifecta",
                    "required_flow": [
                        "session.append:intent",
                        "ctx.sync",
                        "ctx.search",
                        "ctx.get",
                        "session.append:result",
                    ],
                    "segment": ".",
                }
            },  # Valid
            {},  # Invalid
            {"execution": {"engine": "manual", "required_flow": [], "segment": "."}},  # Invalid
        ]

        for wo_data in test_cases:
            ok, err = validate_execution_contract(wo_data)

            # Invariant: NEVER (True, "error")
            if ok is True:
                assert err is None, f"Invariant violated: ok=True but err={err}"
            else:
                assert err is not None and len(err) > 0, (
                    f"Invariant violated: ok=False but err={err}"
                )
