#!/usr/bin/env python3
"""
Schema validation using domain WorkOrder entity.

This module provides schema validation for Work Order YAML files using the
domain's WorkOrder entity for business logic validation.
"""

from pathlib import Path
import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, final

import yaml
from jsonschema import validate as jsonschema_validate

# Domain imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.domain.wo_entities import WorkOrder, WOState, Priority, Governance
from src.domain.result import Result, Ok, Err


@final
class SchemaError(ABC):
    """Base class for schema validation errors (sealed hierarchy)."""

    @abstractmethod
    def message(self) -> str:
        """Return human-readable error message."""
        ...


@dataclass(frozen=True)
class SchemaValidationError(SchemaError):
    """JSON schema validation failed."""

    detail: str

    def message(self) -> str:
        return f"Schema validation failed: {self.detail}"


@dataclass(frozen=True)
class EntityValidationError(SchemaError):
    """WorkOrder entity validation failed."""

    detail: str

    def message(self) -> str:
        return f"Entity validation failed: {self.detail}"


@dataclass(frozen=True)
class DataStructureError(SchemaError):
    """Data structure error (missing field, type mismatch)."""

    detail: str

    def message(self) -> str:
        return f"Data structure error: {self.detail}"


@dataclass(frozen=True)
class YamlLoadError(SchemaError):
    """Failed to load YAML file."""

    detail: str

    def message(self) -> str:
        return f"Failed to load YAML: {self.detail}"


def load_schema(root: Path) -> dict:
    """Load work order schema from docs/backlog/schema."""
    schema_path = root / "docs/backlog/schema/work_order.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return json.loads(schema_path.read_text())


def _priority_from_string(value: str) -> Priority:
    """Convert priority string to Priority enum."""
    if isinstance(value, Priority):
        return value

    # Legacy P0-P3 mapping
    legacy_map = {
        "P0": Priority.CRITICAL,
        "P1": Priority.HIGH,
        "P2": Priority.MEDIUM,
        "P3": Priority.LOW,
        "p0": Priority.CRITICAL,
        "p1": Priority.HIGH,
        "p2": Priority.MEDIUM,
        "p3": Priority.LOW,
    }

    if value in legacy_map:
        return legacy_map[value]

    try:
        return Priority(value.lower())
    except ValueError:
        raise ValueError(
            f"Invalid priority: '{value}'. Must be one of: critical, high, medium, low, P0-P3"
        )


def _state_from_string(value: str) -> WOState:
    """Convert state string to WOState enum."""
    if isinstance(value, WOState):
        return value

    try:
        return WOState(value.lower())
    except ValueError:
        raise ValueError(
            f"Invalid state: '{value}'. Must be one of: pending, running, done, failed, partial"
        )


def _parse_datetime(value: Optional[str | datetime]) -> Optional[datetime]:
    """Parse ISO 8601 datetime string to datetime object.

    Args:
        value: ISO 8601 string, datetime object, or None

    Returns:
        datetime object or None if value is None/empty

    Raises:
        ValueError: If string format is invalid
    """
    if value is None or value == "":
        return None

    # Handle ISO 8601 formats with or without timezone
    # Python's fromisoformat handles: 2026-01-14T10:30:00+00:00
    # But we need to ensure timezone info is present
    if isinstance(value, datetime):
        return value

    try:
        dt = datetime.fromisoformat(value)
        # Ensure timezone-aware (default to UTC if missing)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError as e:
        raise ValueError(
            f"Invalid datetime format: '{value}'. Expected ISO 8601 format (e.g., 2026-01-14T10:30:00+00:00)"
        ) from e


def _normalize_datetimes_for_schema(wo_data: dict) -> dict:
    """Convert datetime objects to ISO 8601 strings for JSON schema validation.

    PyYAML auto-converts ISO 8601 strings to datetime objects during loading.
    The JSON schema expects strings, so we convert them back before validation.

    Args:
        wo_data: WO data from YAML file (may contain datetime objects)

    Returns:
        Copy of wo_data with datetime objects converted to ISO 8601 strings
    """
    datetime_fields = ["started_at", "finished_at", "closed_at"]
    normalized = {}

    for key, value in wo_data.items():
        if key in datetime_fields and isinstance(value, datetime):
            # Convert datetime to ISO 8601 string
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value

    return normalized


def validate_wo_yaml(wo_data: dict, schema: dict) -> Result[WorkOrder, SchemaError]:
    """
    Validate WO YAML against schema using domain entity.

    Args:
        wo_data: WO data from YAML file
        schema: JSON schema for validation

    Returns:
        Ok(WorkOrder) if valid, Err(SchemaError) if invalid
    """
    # Normalize datetime objects to strings for JSON schema validation
    # (PyYAML auto-converts ISO 8601 strings to datetime objects)
    normalized_data = _normalize_datetimes_for_schema(wo_data)

    # First, validate against JSON schema
    try:
        jsonschema_validate(instance=normalized_data, schema=schema)
    except Exception as e:
        return Err(SchemaValidationError(detail=str(e)))

    # Convert types for domain entity
    try:
        priority = _priority_from_string(wo_data.get("priority", "medium"))
        status = _state_from_string(wo_data.get("status", "pending"))

        # Convert dependencies list to tuple
        deps_list = wo_data.get("dependencies", [])
        dependencies = tuple(deps_list) if isinstance(deps_list, list) else ()

        # Parse governance field
        governance = None
        governance_data = wo_data.get("governance")
        if governance_data is not None:
            if isinstance(governance_data, dict):
                must_list = governance_data.get("must", [])
                must_tuple = tuple(must_list) if isinstance(must_list, list) else ()
                governance = Governance(must=must_tuple)
            else:
                return Err(DataStructureError(detail="governance must be a dict with 'must' field"))

        # Parse run_ids as tuple
        run_ids_list = wo_data.get("run_ids", [])
        run_ids = tuple(run_ids_list) if isinstance(run_ids_list, list) else ()

        # Create WorkOrder entity (triggers __post_init__ validation)
        wo = WorkOrder(
            id=wo_data["id"],
            epic_id=wo_data.get("epic_id", ""),
            title=wo_data.get("title", ""),
            priority=priority,
            status=status,
            owner=wo_data.get("owner"),
            dod_id=wo_data.get("dod_id", ""),
            dependencies=dependencies,
            governance=governance,
            run_ids=run_ids,
            started_at=_parse_datetime(wo_data.get("started_at")),
            finished_at=_parse_datetime(wo_data.get("finished_at")),
            closed_at=_parse_datetime(wo_data.get("closed_at")),
            branch=wo_data.get("branch"),
            worktree=wo_data.get("worktree"),
        )
        return Ok(wo)

    except ValueError as e:
        # Expected validation errors from __post_init__ or enum conversion
        return Err(EntityValidationError(detail=str(e)))
    except (KeyError, TypeError) as e:
        # Expected errors from missing fields or type mismatches
        return Err(DataStructureError(detail=str(e)))


def validate_all_wo_files(root: Path) -> dict[str, Result[WorkOrder, SchemaError]]:
    """
    Validate all WO files in the system.

    Args:
        root: Repository root path

    Returns:
        Dictionary mapping WO IDs to validation results
    """
    schema = load_schema(root)
    results = {}

    for state in ["pending", "running", "done", "failed", "partial"]:
        state_dir = root / "_ctx/jobs" / state
        if not state_dir.exists():
            continue

        for wo_file in state_dir.glob("WO-*.yaml"):
            try:
                wo_data = yaml.safe_load(wo_file.read_text())
                wo_id = wo_data.get("id", wo_file.stem)
                results[wo_id] = validate_wo_yaml(wo_data, schema)
            except Exception as e:
                wo_id = wo_file.stem
                results[wo_id] = Err(YamlLoadError(detail=str(e)))

    return results


def main():
    """CLI entry point for schema validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate WO files against schema")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--wo-id", help="Specific WO ID to validate")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.wo_id:
        # Validate single WO
        for state in ["pending", "running", "done", "failed", "partial"]:
            wo_path = root / "_ctx/jobs" / state / f"{args.wo_id}.yaml"
            if wo_path.exists():
                schema = load_schema(root)
                wo_data = yaml.safe_load(wo_path.read_text())
                result = validate_wo_yaml(wo_data, schema)
                if result.is_ok():
                    print(f"{args.wo_id}: PASSED")
                    return 0
                else:
                    error = result.unwrap_err()
                    print(f"{args.wo_id}: FAILED - {error.message()}")
                    return 1
        print(f"{args.wo_id}: NOT FOUND")
        return 1
    else:
        # Validate all WOs
        results = validate_all_wo_files(root)

        passed = sum(1 for r in results.values() if r.is_ok())
        failed = len(results) - passed

        for wo_id, result in results.items():
            if result.is_ok():
                print(f"{wo_id}: PASSED")
            else:
                error = result.unwrap_err()
                print(f"{wo_id}: FAILED - {error.message()}")

        print(f"\nSummary: {passed} PASSED, {failed} FAILED")
        return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
