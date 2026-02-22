# WO Gates Hardening Implementation Plan (Upgraded)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix severe P0 state corruption and concurrency issues in the Trifecta WO CLI by making state transitions atomic, fixing lock TTL issues, enforcing session marker consistency, and making index rebuilds atomic.

**Architecture:**

1. **Atomic Writes:** Use `tempfile.NamedTemporaryFile` in the same directory, run `os.fsync`, and then use `os.replace`.
2. **Atomic Backups:** When replacing files, backup the original as `WO-XXXX.yaml.bak.<timestamp>` so that multiple updates or retries don't collide or lose information.
3. **Locking:** Explicit lock TTL checking logic defaulting to 86400s (24h) with safe integer parsing fallback from an environment variable `WO_LOCK_TTL_SEC`.
4. **Session Markers:** Create a Single Source of Truth (SSOT) for session markers in `helpers.py` or domain entities.
5. **Index Atomicity:** Ensure `export_wo_index.py` also writes its JSON atomically.
6. **Reconciler Update:** `ctx_reconcile_state.py` must explicitly ignore `.bak.*` files.

**Tech Stack:** Python 3.12+, `os` primitives, YAML, Monkeypatching for tests.

---

### Task 1: Component WO-A - Atomic YAML Utilities

**Files:**

- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/helpers.py`

**Implementation:**
Implement robust, concurrency-safe file operations in `helpers.py`:

- `atomic_write_yaml(target_path: Path, data: dict)`
  - Creates a `NamedTemporaryFile(dir=target_path.parent, delete=False)`
  - Dumps YAML, flushes, `os.fsync`s, then `os.replace`s.
  - Cleans up orphaned temp file on exception.
- `atomic_replace_with_backup(src_path: Path)`
  - Uses `os.replace` to move `src_path` to `src_path.with_suffix(f".bak.{int(time.time())}")`.

### Task 2: Component WO-A - Atomic State Transitions in `take` and `finish`

**Files:**

- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/ctx_wo_take.py`
- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/ctx_wo_finish.py`

**Implementation:**

- Replace direct `write_text` and `unlink` with `atomic_write_yaml` and `atomic_replace_with_backup()`.
- Ensure transactions rollbacks handle `.bak` files correctly if needed.

### Task 3: Component WO-H - Atomic Index Export

**Files:**

- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/ctx_export_index.py` (or wherever `export_wo_index` logic lives)

**Implementation:**

- Write the final `_ctx/jobs/index.json` using a `NamedTemporaryFile` + `fsync` + `os.replace` pattern to prevent sidecar from reading truncated JSONs.

### Task 4: Component WO-B - Reconfigure Lock TTLs

**Files:**

- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/helpers.py`
- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_helpers_locks.py` (or similar)

**Implementation:**

- Semantics: `check_lock_age` returns `True` if stale (expired), `False` if active.
- Default to `max_age_seconds = int(os.environ.get("WO_LOCK_TTL_SEC", 86400))`. Use exception handling if `WO_LOCK_TTL_SEC` is invalid (e.g., "abc") and fallback to 86400 safely.
- Write unit tests verifying lock freshness/staleness logic.

### Task 5: Component WO-C - Establish Strict Session Markers SSOT

**Files:**

- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/helpers.py` (or `validators.py`)
- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/ctx_wo_take.py`
- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/ctx_wo_finish.py` (validator logic)

**Implementation:**

- Create `format_session_intent_marker(wo_id: str) -> str` returning `f"[{wo_id}] intent:"` (or similar, depending on exact string requirement).
- Use this SSOT in `take` to write the log, and in `finish` to regex-match the log.

### Task 6: Component WO-I - Update Reconciler for `.bak` files

**Files:**

- Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/ctx_reconcile_state.py`

**Implementation:**

- Tell `ctx_reconcile_state.py` to explicitly ignore `.bak` files when scanning for duplicates or corrupted states.

### Task 7: Verification & Testing (Crash-safety via Monkeypatch)

**Files:**

- Add/Modify: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/integration/test_wo_crash_safety.py`

**Implementation:**

- Write deterministic crash-safety tests by monkeypatching `os.replace` to throw an exception at critical points.
- Verify that 0 copies rule is maintained (either pending, running, or backup exists, never fully lost).
- Verify double copies aren't both considered active.
