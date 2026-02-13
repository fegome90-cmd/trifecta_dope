import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


def _load_schema() -> dict:
    schema_path = Path(__file__).resolve().parents[2] / "docs" / "backlog" / "schema" / "work_order.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _base_wo(*, status: str) -> dict:
    return {
        "version": 1,
        "id": "WO-9001",
        "epic_id": "E-9001",
        "title": "contract test",
        "priority": "P1",
        "status": status,
        "dod_id": "DOD-DEFAULT",
        "scope": {"allow": ["scripts/**"], "deny": [".env*"]},
        "verify": {"commands": ["echo ok"]},
    }


def test_schema_requires_execution_for_pending_wo() -> None:
    schema = _load_schema()
    wo = _base_wo(status="pending")

    with pytest.raises(ValidationError):
        validate(instance=wo, schema=schema)


def test_schema_rejects_non_trifecta_engine_for_running_wo() -> None:
    schema = _load_schema()
    wo = _base_wo(status="running")
    wo["execution"] = {
        "engine": "manual",
        "required_flow": [
            "session.append:intent",
            "ctx.sync",
            "ctx.search",
            "ctx.get",
            "session.append:result",
        ],
        "segment": ".",
    }

    with pytest.raises(ValidationError):
        validate(instance=wo, schema=schema)


def test_schema_accepts_valid_trifecta_execution_for_pending_wo() -> None:
    schema = _load_schema()
    wo = _base_wo(status="pending")
    wo["execution"] = {
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

    validate(instance=wo, schema=schema)


def test_schema_allows_legacy_done_wo_without_execution() -> None:
    schema = _load_schema()
    wo = _base_wo(status="done")

    validate(instance=wo, schema=schema)
