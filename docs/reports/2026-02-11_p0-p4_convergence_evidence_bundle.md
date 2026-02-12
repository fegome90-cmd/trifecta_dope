# P0-P4 Convergence Evidence Bundle (Worktree)

Date: 2026-02-11
Worktree: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/refiner-p0-segment-ssot`
Branch: `codex/refiner-p0-segment-ssot`

## Scope

This bundle summarizes P0-P4 remediation:
- P0: segment state SSOT + build/sync convergence on input resolution
- P1: deterministic bootstrap for create/reset
- P2: build/sync error-card parity for structural preconditions
- P3: persistent AST cache evidence and deterministic cache path handling
- P4: honest CLI contract for hover/snippet capabilities

## P0 - Segment State SSOT

### Problem
`ctx build --segment .` and `ctx sync --segment .` diverged due to inconsistent segment identity derivation.

### Fix
- Added segment resolver: `src/infrastructure/segment_state.py`
- Added typed errors:
  - `InvalidSegmentPathError`
  - `InvalidConfigScopeError`
- Integrated resolver into build/sync preconditions in `src/infrastructure/cli.py`
- Added SSOT fields in telemetry payload:
  - `segment_id_resolved`
  - `segment_root_resolved`
  - `segment_state_source`

### Evidence
- `tests/unit/test_segment_state_resolution.py`
- `tests/unit/test_cli_fp_gate.py` (dot-vs-abs parity and invalid path card)

## P1 - Bootstrap Determinism

### Problem
`create` produced a segment not immediately operable for `ctx build` / `ctx reset --force`.

### Fix
- `create` now writes:
  - `AGENTS.md`
  - `_ctx/trifecta_config.json`
  - north-star files with suffixed names
- `ctx reset` now regenerates north-star files (`agent_<id>`, `prime_<id>`, `session_<id>`), not legacy `agent.md`.
- Formal postcondition added in create command docstring.
- Added bootstrap telemetry:
  - `segment_bootstrap_version`
  - `bootstrap_missing_artifacts_count`

### Evidence
- `tests/unit/test_cli_create_naming.py`
- `tests/acceptance/test_ctx_sync_preconditions.py::test_create_allows_immediate_ctx_reset`

## P2 - Error Card Parity

### Problem
Same structural precondition emitted different codes in build vs sync.

### Fix
- Added shared classifier in `src/infrastructure/cli.py`:
  - `_classify_north_star_precondition(errors)`
- Applied in both build and sync.
- Sync now validates north-star structure before build path.
- Preserved UX for `SEGMENT_NOT_INITIALIZED` next-steps (`create`, `refresh-prime`).

### Evidence
- `tests/unit/test_cli_fp_gate.py::test_ctx_build_and_sync_emit_same_precondition_code`
- `tests/acceptance/test_ctx_sync_preconditions.py`

## P3 - AST Persist Cache Evidence

### Problem
Cache persistence evidence was ambiguous in some runs (perceived miss behavior), and cache DB path handling depended on cwd in parts of CLI.

### Fix
- Added deterministic DB-path helper in factory:
  - `get_ast_cache_db_path(segment_id)`
- Reused same DB path in:
  - `ast symbols`
  - `ast cache-stats`
  - `ast clear-cache`
- Added explicit observability in `ast symbols` output:
  - `miss_reason`
  - `cache_db_path`

### Evidence
- `tests/unit/test_cli_ast_cache_observability.py`
- Manual CLI verification:
  - Run1: `cache_status=miss`, `miss_reason=cold_cache_empty`
  - Run2: `cache_status=hit`, `miss_reason=cache_hit`

## P4 - Honest Hover/Snippet Contract

### Problem
`ast snippet` silently succeeded while unimplemented; `ast hover` returned stub data without explicit capability metadata.

### Fix
- `ast snippet` now fail-closed with structured error:
  - `status=error`
  - `error_code=NOT_IMPLEMENTED`
  - `message`, `hint`, `context`
  - exit code `1`
- `ast hover` now advertises stub capability explicitly:
  - `backend=wip_stub`
  - `capability_state=WIP`
  - `response_state=partial`
- Added telemetry counters/events:
  - `ast.snippet.not_implemented`
  - `ast.hover.wip`

### Evidence
- `tests/unit/test_cli_ast_contracts.py`
- Runtime JSON output checks for hover/snippet

## Verification Summary

Executed and passing in this worktree:
- `uv run pytest -q tests/unit/test_cli_fp_gate.py tests/unit/test_segment_state_resolution.py tests/unit/test_cli_create_naming.py tests/unit/test_cli_ast_cache_observability.py tests/unit/test_cli_ast_contracts.py tests/acceptance/test_ctx_sync_preconditions.py`
  - Result: `25 passed`
- `uv run mypy` (focal files)
  - Result: no issues
- `uv run ruff check` (focal files)
  - Result: no issues

## Risk / Residual

- Risk level: low-to-moderate
- Main behavior changes are contract clarifications and stricter precondition handling; existing consumers relying on silent snippet success now receive explicit failure (intentional fail-closed).
- Hover remains stub by design but now truthfully labeled.

## Merge Strategy

- Prefer atomic commits per cycle (P0/P1/P2/P3/P4) for auditability.
- Keep telemetry data file churn (`_ctx/telemetry/*`) out of functional commits.
