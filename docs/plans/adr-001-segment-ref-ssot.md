# ADR: SegmentRef SSOT

## Status
Accepted

## Context
Trifecta needs a single source of truth for resolving segment identity from any path. Multiple parts of the codebase were computing segment IDs manually, leading to inconsistencies.

## Decision
We will use `resolve_segment_ref()` from `src/domain/segment_resolver.py` as the SSOT for segment identity.

The `SegmentRef` object provides:
- `root_abs`: Absolute canonical path
- `slug`: Human-readable name
- `fingerprint`: Hash-based unique ID
- `id`: Combined slug_fingerprint

## Consequences
- All code must use `resolve_segment_ref()` to get segment identity
- Legacy functions deprecated with warnings
- Contracts documented in `src/platform/contracts.py`
