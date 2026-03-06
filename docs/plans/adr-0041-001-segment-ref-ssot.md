# ADR-0041-001: SegmentRef as Single Source of Truth

**Date**: 2026-03-06
**Status**: Proposed
**Epic**: E-V1 (Trifecta V1 Global Platform)
**WO**: WO-0041

## Context

Currently, Trifecta has multiple places where segment identity is computed:
- `segment_resolver.py` with `resolve_segment_ref()` - produces `SegmentRef(slug, fingerprint, id)`
- Various modules computing `repo_id` and `segment_id` independently
- No unified contract for segment directory paths (runtime_dir, telemetry_dir, cache_dir, etc.)

This leads to:
- Inconsistent ID computation across modules
- No clear ownership of segment identity
- Difficulty in testing and verifying correctness

## Decision

We will establish `SegmentRef` as the Single Source of Truth (SSOT) for all segment identity concerns:

### Core Contract (frozen dataclass)

```python
@dataclass(frozen=True)
class SegmentRef:
    repo_root: Path              # Canonical repo root
    repo_id: str                 # hash(canonical_path) - stable across renames
    segment_root: Path           # Canonical segment root
    segment_id: str              # Runtime key (slug_fingerprint)
    runtime_dir: Path            # Platform-specific runtime data
    registry_key: str            # Key for registry lookups
    telemetry_dir: Path         # Telemetry events storage
    config_dir: Path            # Configuration directory
    cache_dir: Path             # Cache directory
```

### Resolver Function

```python
def resolve_segment_ref(
    segment_input: Optional[Path | str] = None,
    hash_length: int = 8,
) -> SegmentRef:
    """
    Resolve segment identity from any input path.
    
    This is the SINGLE SOURCE OF TRUTH for segment identity.
    All modules MUST use this function instead of computing IDs directly.
    """
```

## Consequences

### Positive
- **Single point of truth**: All segment identity from one function
- **Testability**: Easy to mock/test in isolation
- **Consistency**: Same ID computation everywhere
- **Maintainability**: One place to change identity logic

### Negative
- **Migration cost**: Existing code must migrate to use resolver
- **Deprecation warnings**: Old functions must emit warnings

## Implementation Notes

1. Keep existing `SegmentRef` from `segment_resolver.py` but extend it
2. Add deprecation warnings to any function that computes IDs directly
3. Create contract tests to verify all use cases use the resolver

## Related

- WO-0041: SSOT + Contratos + Skeleton
- WO-0042: CLI Adelgazado + Repo Commands (uses SSOT)
- WO-0043: SQLite + Daemon + Operación Real (uses SSOT)
