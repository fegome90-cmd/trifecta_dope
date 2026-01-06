# Telemetry Environment Contracts

This document defines the behavior of the Telemetry system regarding environment variables and worktree isolation.

## Precedence Rules

1.  **`TRIFECTA_NO_TELEMETRY=1` (Highest Priority)**
    - Mandatory NO-OP mode.
    - Behavior: `Telemetry` instance sets `level = "off"`.
    - No directories are created.
    - No file writes are performed.
    - Overrides all other settings.

2.  **`level="off"` (Argument Priority)**
    - Explicitly disables telemetry for a specific instance.
    - Behavior: Similar to `TRIFECTA_NO_TELEMETRY`.

3.  **`TRIFECTA_TELEMETRY_DIR=<path>` (Redirection Priority)**
    - Redirects all telemetry writes to a custom path.
    - Behavior: Used by `test-gate` to isolate test side-effects.
    - Writes go to `<path>`, and the repository's `_ctx/telemetry` is **NEVER** touched.

4.  **`Default`**
    - Telemetry is written to the segment's `_ctx/telemetry` directory.

## Implementation Details

- **Atomic Writes**: All telemetry writes are non-destructive (append for `events.jsonl`, overwrite for `last_run.json`).
- **Isolation**: During `pre-commit`, either NO-OP or Redirection MUST be active to ensure a clean worktree.
- **Cleanup**: Redirected telemetry in `/tmp` should be cleaned up by the triggering script (e.g., using `trap EXIT`).

---

# Test Gate Contracts

This section defines the test gate contracts for Trifecta Dope development.

## Gate Definitions

### gate-quick (Fast Feedback)

**Purpose:** Quick iteration during development - excludes slow E2E tests

**Scope:**
- Unit tests (`tests/unit/`)
- Integration tests (`tests/integration/`)
- **Excludes:** Acceptance/E2E tests (includes known pre-existing failures)

**Command:**
```bash
uv run pytest tests/unit/ tests/integration/ -v
```

**Expected Behavior:** Fast pass/fail feedback (<30 seconds)

**Use When:**
- Active development
- Pre-commit checks
- CI fast-fail lane

---

### gate-all (Full Verification)

**Purpose:** Complete test suite including acceptance tests

**Scope:**
- Unit tests (`tests/unit/`)
- Integration tests (`tests/integration/`)
- Acceptance/E2E tests (`tests/acceptance/`)
- **Known Failures:** Documented in `docs/reports/KNOWN_FAILS.md`

**Command:**
```bash
# Run all tests (including acceptance)
uv run pytest -v

# Skip specific known failures (example)
uv run pytest -v --deselect tests/acceptance/test_pd_evidence_stop_e2e.py::test_e2e_evidence_stop_real_cli
```

**Expected Behavior:** Full suite validation, may include known failures

**Use When:**
- Pre-merge validation
- Release preparation
- Complete regression testing

---

## Known Failures

See `docs/reports/KNOWN_FAILS.md` for documented pre-existing test failures.

**Current Known Failures:**
- `test_e2e_evidence_stop_real_cli` - Pre-existing (verified against base commit `bd26190`)

---

## Gate Policy

1. **gate-quick MUST PASS** before committing
2. **gate-all** reviewed for new failures before merge
3. **Known failures** documented in KNOWN_FAILS.md before being excluded
4. **New failures** investigated and either:
   - Fixed (regression)
   - Documented in KNOWN_FAILS.md (pre-existing)
   - Added to skip list with justification

---

*Test Gates Section Added: 2026-01-05*
