# ADR-003: Schema Evolution for required_flow

## Status

**ACCEPTED** (2026-02-21)

## Context

The `required_flow` constraint was added to the Work Order schema to enforce Trifecta CLI usage patterns. The full flow requires:

```yaml
required_flow:
  - session.append:intent
  - ctx.sync
  - ctx.search
  - ctx.get
  - session.append:result
```

**Problem**: 25 WOs in `done` state have `required_flow: [verify]` instead of the full flow. These WOs were completed **before** the schema enforced the complete Trifecta workflow.

Applying the current schema to historical WOs would create:

- **False compliance claims**: Steps listed but never executed
- **Audit integrity issues**: Records would not reflect actual execution
- **Migration complexity**: `session.md` files may not exist for historical WOs

## Decision

Implement a **hybrid approach** combining schema exemption with explicit legacy marking:

### 1. Conditional Schema Validation

The schema validates `required_flow` differently based on WO status:

| Status | required_flow Validation |
|--------|--------------------------|
| `pending`, `running` | Full flow required (5 steps) |
| `done`, `failed` | Minimum 1 item required |

### 2. Legacy Marker

Historical WOs receive an explicit marker:

```yaml
execution:
  engine: trifecta
  required_flow:
    - verify
  x_legacy_flow: true  # Marker for transition period
  segment: .
```

### 3. Prospective Enforcement

New WOs (created after this ADR) must follow the full flow. The schema enforces this at creation time.

## Schema Changes

### Before (Uniform Validation)

```json
"required_flow": {
  "type": "array",
  "items": {"type": "string"},
  "allOf": [
    {"contains": {"const": "session.append:intent"}},
    {"contains": {"const": "ctx.sync"}},
    {"contains": {"const": "ctx.search"}},
    {"contains": {"const": "ctx.get"}},
    {"contains": {"const": "session.append:result"}}
  ]
}
```

### After (Conditional Validation)

```json
"allOf": [
  {
    "if": {"properties": {"status": {"enum": ["pending", "running"]}}},
    "then": {
      "properties": {
        "execution": {
          "properties": {
            "required_flow": {
              "allOf": [
                {"contains": {"const": "session.append:intent"}},
                {"contains": {"const": "ctx.sync"}},
                {"contains": {"const": "ctx.search"}},
                {"contains": {"const": "ctx.get"}},
                {"contains": {"const": "session.append:result"}}
              ]
            }
          }
        }
      }
    }
  },
  {
    "if": {"properties": {"status": {"enum": ["done", "failed"]}}},
    "then": {
      "properties": {
        "execution": {
          "properties": {
            "required_flow": {"minItems": 1}
          }
        }
      }
    }
  }
]
```

## Consequences

### Positive

1. **Historical Integrity**: Records remain accurate to what was actually executed
2. **No False Compliance**: We don't claim steps that weren't run
3. **Clear Audit Trail**: `x_legacy_flow: true` documents the transition
4. **Prospective Enforcement**: New WOs must follow full workflow
5. **Reduced Scope**: WO-0019 scope reduced from 43 to 18 WOs

### Negative

1. **Schema Complexity**: Two validation paths increase cognitive load
2. **Migration Effort**: Need to add `x_legacy_flow` marker to 25 WOs
3. **Documentation Burden**: Need to explain legacy vs. current in guides

### Mitigations

- Schema comments document the conditional logic
- ADR serves as permanent record of the decision
- `x_legacy_flow` marker is optional but recommended for clarity

## Implementation

1. **Schema Update**: [`docs/backlog/schema/work_order.schema.json`](../backlog/schema/work_order.schema.json)
2. **Legacy Marker Script**: Add `x_legacy_flow: true` to affected WOs
3. **Validation Update**: [`scripts/schema_validation.py`](../../scripts/schema_validation.py)
4. **WO-0019 Scope Update**: Remove Category A from scope

## Affected WOs

25 WOs in `done/` directory with `required_flow: [verify]`:

- WO-0001 through WO-0025 (historical, completed before schema enforcement)

## References

- [Work Order Schema](../backlog/schema/work_order.schema.json)
- [WO Governance (ADR-002)](ADR-002-wo-governance.md)
- [WO Workflow](../backlog/WORKFLOW.md)
