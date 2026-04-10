# ADR-004: Segment Canon Authority and Create Contract

**Status**: ACCEPTED  
**Date**: 2026-03-19

## Context

The WO/lifecycle/harness program needs a frozen, executable contract for how a segment is recognized as canonical before the resolver and `create` implementation are changed.

This decision closes the remaining authority gap between:

- the current platform state,
- local bootstrap config, and
- directory-name fallback behavior.

The program now distinguishes between:

- the **operational SSOT** for the current platform, and
- the **transitional bootstrap mechanisms** used only when a real canonical candidate does not yet exist.

## Decision

### 1) Operational SSOT

The final operational SSOT for the current platform is the **top-level tracked `_ctx/` triplet**:

- `_ctx/agent_<segment>.md`
- `_ctx/prime_<segment>.md`
- `_ctx/session_<segment>.md`

This triplet is the canonical authority surface for the segment on the current platform.

### 2) Local config is transitional only

`_ctx/trifecta_config.json` is transitional bootstrap/configuration support only.

It may help bootstrap or preserve compatibility, but it is **not** the final authority over canonical segment identity when a tracked top-level `_ctx/` triplet is present.

### 3) `dirname(...)` is bootstrap-only

`dirname(...)`-style derivation is allowed only for **real bootstrap** when no versioned canonical candidate exists yet.

It must not override an existing tracked canonical candidate, and it must not be used to reinterpret a segment that is already initialized.

### 4) Canonical candidate eligibility

A candidate may be treated as canonical only if it is:

- versioned / tracked in git, and
- physically present on disk at evaluation time.

**Deleted or stale indexed paths do not count as present.**

For the current platform, the only legacy singleton blockers are the top-level `_ctx/agent.md`, `_ctx/prime.md`, and `_ctx/session.md` forms; they are not the final canonical surface.

### 5) `create` has a write-zero contract on non-bootstrap states

`create` must fail closed before writing when it detects any initialized or conflicting canonical state.

This includes cases where a canonical candidate already exists, is incomplete, is ambiguous, is contaminated, or is contradicted by local config.

`create` may bootstrap a directory only when no canonical candidate exists and the directory is truly uninitialized. In that case, the positive bootstrap path is allowed; `SEGMENT_CANON_MISSING` belongs to resolver / non-bootstrap operations.

The contract is **write-zero** for all semantic failure paths of `create`: no partial bootstrap files, no config rewrites, and no silent repair writes. For the current batch, those failure paths must not write any of the following surfaces:

- `AGENTS.md`
- `skill.md`
- `readme_tf.md`
- `_ctx/trifecta_config.json`
- `_ctx/agent_*.md`
- `_ctx/prime_*.md`
- `_ctx/session_*.md`

## Error Taxonomy

The frozen resolver/create contract must expose the following segment-canon error conditions:

| Error | Meaning |
|---|---|
| `SEGMENT_CANON_MISSING` | No canonical candidate can be established from the current platform state during a non-bootstrap operation. |
| `SEGMENT_CANON_INCOMPLETE` | A candidate exists, but the tracked top-level `_ctx/` triplet is incomplete or missing required members. |
| `SEGMENT_CANON_AMBIGUOUS` | More than one plausible canonical candidate exists, or resolution cannot choose a single versioned root. |
| `SEGMENT_CANON_CONTAMINATED` | The candidate is polluted by unexpected or conflicting files/state. |
| `SEGMENT_CANON_CONTRADICTED_BY_LOCAL_CONFIG` | Transitional local config points to a different root than the canonical candidate. |
| `SEGMENT_ALREADY_INITIALIZED` | `create` was invoked on a segment that is already initialized and must not be rewritten. |

All six conditions are fail-closed. `SEGMENT_ALREADY_INITIALIZED` is the write-zero rejection path for `create`.

## Contract Notes

- The resolver must prefer the versioned, physically present canonical candidate over any stale index entry.
- Transitional local config can help bootstrap, but it cannot supersede a tracked canonical candidate.
- `create` may only write after preflight succeeds and the target is proven to be a true bootstrap case.

## Contract Test Batch to Create / Adjust Before Implementation

| Test name | Suggested file | Case | Expected error | Severity |
|---|---|---|---|---|
| `test_resolver_prefers_tracked_top_level_ctx_triplet` | `tests/unit/test_segment_resolver.py` | A versioned top-level `_ctx/{agent,prime,session}_<segment>.md` triplet exists and should be selected as canonical. | none | high |
| `test_resolver_ignores_stale_deleted_index_entry` | `tests/unit/test_segment_resolver.py` | An indexed path points to a deleted candidate and no other canonical candidate exists. | `SEGMENT_CANON_MISSING` | high |
| `test_resolver_fails_when_ctx_triplet_incomplete` | `tests/unit/test_segment_resolver.py` | One or more files from the tracked triplet are missing. | `SEGMENT_CANON_INCOMPLETE` | high |
| `test_resolver_fails_when_multiple_versioned_candidates_exist` | `tests/unit/test_segment_resolver.py` | More than one versioned canonical candidate is discoverable. | `SEGMENT_CANON_AMBIGUOUS` | high |
| `test_resolver_fails_when_candidate_is_contaminated_by_nontracked_canonical_family_file` | `tests/unit/test_segment_resolver.py` | Canonical candidate is polluted by a nontracked file in the canonical family. | `SEGMENT_CANON_CONTAMINATED` | high |
| `test_resolver_fails_when_candidate_is_contaminated_by_legacy_singleton` | `tests/unit/test_segment_resolver.py` | Canonical candidate is polluted by a top-level legacy singleton such as `_ctx/agent.md`, `_ctx/prime.md`, or `_ctx/session.md`. | `SEGMENT_CANON_CONTAMINATED` | high |
| `test_resolver_fails_when_local_config_disagrees_with_tracked_candidate` | `tests/unit/test_segment_state_resolution.py` | Transitional config points to a different root than the tracked canonical candidate. | `SEGMENT_CANON_CONTRADICTED_BY_LOCAL_CONFIG` | high |
| `test_resolver_ignores_versioned_path_when_not_physically_present` | `tests/unit/test_segment_resolver.py` | A path is versioned in the index but does not exist physically on disk. | `SEGMENT_CANON_MISSING` | high |
| `test_create_allows_true_bootstrap_when_directory_is_uninitialized` | `tests/unit/test_cli_create_naming.py` | `create` is run in a truly uninitialized directory and no canonical candidate exists. | none; bootstrap succeeds | critical |
| `test_create_returns_already_initialized_without_writing` | `tests/unit/test_cli_create_naming.py` | `create` is run against an already initialized segment. | `SEGMENT_ALREADY_INITIALIZED` | critical |
| `test_create_fails_when_canonical_candidate_is_incomplete` | `tests/unit/test_cli_create_naming.py` | `create` runs against a partially bootstrapped tracked triplet. | `SEGMENT_CANON_INCOMPLETE` | critical |
| `test_create_fails_when_canonical_candidate_is_ambiguous` | `tests/unit/test_cli_create_naming.py` | `create` runs when more than one versioned candidate exists. | `SEGMENT_CANON_AMBIGUOUS` | critical |
| `test_create_fails_when_canonical_candidate_is_contaminated` | `tests/unit/test_cli_create_naming.py` | `create` runs against a polluted canonical candidate. | `SEGMENT_CANON_CONTAMINATED` | critical |
| `test_create_fails_when_local_config_contradicts_canonical_candidate` | `tests/unit/test_cli_create_naming.py` | `create` runs when local config points to a different root. | `SEGMENT_CANON_CONTRADICTED_BY_LOCAL_CONFIG` | critical |

### Write-zero assertion for `create`

The `create` tests must verify that no bootstrap files are created on failure outside the true bootstrap path:

- no `AGENTS.md`
- no `skill.md`
- no `readme_tf.md`
- no `_ctx/trifecta_config.json`
- no `_ctx/agent_*.md`
- no `_ctx/prime_*.md`
- no `_ctx/session_*.md`

## First Implementation Batch Scope

### In scope

1. Resolver:
   - canonical candidate detection
   - tracked top-level `_ctx/` triplet preference
   - stale/deleted path rejection
   - local-config contradiction detection

2. `create`:
   - bootstrap-only path
   - write-zero fail-closed preflight
   - `SEGMENT_ALREADY_INITIALIZED` rejection
   - minimal user-facing error messages

3. Messages:
   - short, actionable, no debate text
   - identify the failing canonical condition

### Out of scope

- resolver implementation details beyond the canonical candidate contract
- broad CLI/help rewrites
- roadmap changes outside the anchor reference
- non-essential refactors in unrelated segment helpers
- changes to telemetry, audit, or WO lifecycle scripts
- separating repo bootstrap from segment bootstrap; that remains future work and is not solved in this batch

## Consequences

### Positive

- freezes the segment-canon authority model before code changes
- makes bootstrap behavior explicit and narrow
- gives contract tests a precise fail-closed target
- current batch guardrails must cover the full legacy write surface because repo bootstrap vs segment bootstrap is deferred

### Negative

- existing fallback behavior may need to be removed or narrowed
- stale indexed paths that used to “work” must now fail closed

## References

- [`docs/plans/WO-LIFECYCLE-HARNESS-ANCHOR.md`](../plans/WO-LIFECYCLE-HARNESS-ANCHOR.md)
- [`src/infrastructure/cli.py`](../../src/infrastructure/cli.py)
- [`src/infrastructure/segment_state.py`](../../src/infrastructure/segment_state.py)
- [`src/trifecta/domain/segment_ref.py`](../../src/trifecta/domain/segment_ref.py)
- [`tests/contracts/test_segment_ref_contract.py`](../../tests/contracts/test_segment_ref_contract.py)
- [`tests/unit/test_segment_resolver.py`](../../tests/unit/test_segment_resolver.py)
