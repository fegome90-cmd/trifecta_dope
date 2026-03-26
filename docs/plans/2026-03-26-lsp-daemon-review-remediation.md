# LSP Daemon Review Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the official daemon lifecycle surface against resource leaks and stale process artifacts, while addressing low-risk hygiene findings from the 2026-03-26 LSP + Daemon review.

**Architecture:** Keep the patch scoped to the current operational authority (`src/platform/daemon_manager.py`) and low-risk hygiene fixes. Treat the review report as feedback to verify, not blindly apply: fix confirmed lifecycle defects now, defer broader architectural refactors to follow-up work, and explicitly reject stale or already-resolved findings.

**Tech Stack:** Python 3.12+, pytest, mypy --strict, ruff, Trifecta CLI context workflow.

---

## Verified Scope Decisions

### Fix now
- `CRIT-1` File handle ownership leak in `DaemonManager.start()`.
- `CRIT-2` PID file race in `DaemonManager.start()` when socket appears but child process is already dead.
- `IMP-5` Unconditional cleanup in `DaemonManager.stop()` that can erase artifacts while a daemon may still be alive.
- `IMP-2` Malformed docstring in `src/infrastructure/daemon_paths.py`.
- `SUG-2` Missing unit coverage for `LSPClient.start()` failure paths (only if it stays small and does not force unrelated refactors).

### Defer to follow-up change
- `IMP-1` Clean Architecture refactor in `src/application/daemon_use_case.py` (real issue, but broader than this lifecycle hardening batch).
- `IMP-4` `_lock_fp` typing in `src/infrastructure/lsp_daemon.py` (valid hygiene item, but the file is explicitly marked reference-only, not official daemon authority).
- `SUG-1` Deprecated `src/application/lsp_manager.py` cleanup.
- `SUG-3` Redundant protocol cleanup in `src/platform/runtime_manager.py`.

### Reject / no-op in this worktree
- `IMP-3` Misplaced `request()` docstring in `src/infrastructure/lsp_client.py` is already fixed in the worktree (`request()` docstring is immediately below the function signature).

---

### Task 1: Harden `DaemonManager.start()` resource ownership and PID publication

**Files:**
- Modify: `src/platform/daemon_manager.py:49-95`
- Test: `tests/unit/test_daemon_manager.py`
- Reference: `tests/integration/daemon/test_daemon_manager.py`

**Step 1: Write the failing tests**

Add focused unit tests for:

```python
def test_start_closes_log_handle_after_spawn(...):
    ...


def test_start_does_not_write_pid_when_child_exits_before_ready(...):
    ...
```

The first test should verify the parent-owned file object is closed after `subprocess.Popen(...)` returns. The second should simulate `socket_path.exists() == True` while `proc.poll()` returns a non-`None` exit status, then assert `start()` returns `False` and no PID file is written.

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_daemon_manager.py -k "log_handle or pid" -v
```

Expected: FAIL because `start()` currently never closes `log_file` and writes the PID without checking `proc.poll()`.

**Step 3: Write minimal implementation**

Update `DaemonManager.start()` so that:

```python
log_file = self._log_path.open("a")
try:
    proc = subprocess.Popen(..., stdout=log_file, ...)
finally:
    log_file.close()

for _ in range(self.DAEMON_START_TIMEOUT * 10):
    if self._socket_path.exists():
        if proc.poll() is None:
            self._pid_path.write_text(str(proc.pid))
            return True
        return False
```

Keep singleton lock release in `finally`, and preserve current runtime-dir / env behavior.

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/unit/test_daemon_manager.py -k "log_handle or pid" -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/platform/daemon_manager.py tests/unit/test_daemon_manager.py
git commit -m "fix: harden daemon start lifecycle"
```

---

### Task 2: Make `DaemonManager.stop()` cleanup conditional on verified death

**Files:**
- Modify: `src/platform/daemon_manager.py:96-185`
- Test: `tests/unit/test_daemon_manager.py`
- Reference: `tests/integration/daemon/test_daemon_manager.py`

**Step 1: Write the failing tests**

Add tests for the cleanup contract:

```python
def test_stop_keeps_pid_and_socket_when_process_survives_kill(...):
    ...


def test_stop_cleans_files_once_process_is_gone(...):
    ...
```

The first test should simulate repeated `is_running() == True` after SIGTERM/SIGKILL and assert `_cleanup_files()` is **not** called. The second should simulate normal shutdown and assert cleanup happens.

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_daemon_manager.py -k "survives_kill or process_is_gone" -v
```

Expected: FAIL because `_cleanup_files()` currently runs unconditionally in `finally`.

**Step 3: Write minimal implementation**

Add a small helper and gate cleanup on it:

```python
def _is_process_alive(self, pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False

...
finally:
    if pid is None or not self._is_process_alive(pid):
        self._cleanup_files()
```

Preserve idempotent `stop()` behavior for missing PID files / already-dead processes.

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/unit/test_daemon_manager.py -k "survives_kill or process_is_gone" -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/platform/daemon_manager.py tests/unit/test_daemon_manager.py
git commit -m "fix: preserve daemon artifacts until process exit"
```

---

### Task 3: Apply low-risk hygiene fixes that are confirmed in the current tree

**Files:**
- Modify: `src/infrastructure/daemon_paths.py:14-27`
- Optional Test: no new test required unless formatting exposes a parser/doc linter issue

**Step 1: Patch the malformed docstring**

Replace the malformed `Raises` block with a valid docstring:

```python
def _validate_daemon_base_dir(tmp_dir: Path) -> None:
    """
    Validate that base directory for daemon files is accessible.

    Raises:
        RuntimeError: If tmp_dir doesn't exist or isn't writable.
    """
```

**Step 2: Run lint/typecheck for touched files**

Run:
```bash
uv run ruff check src/infrastructure/daemon_paths.py src/platform/daemon_manager.py tests/unit/test_daemon_manager.py
uv run mypy src/platform/daemon_manager.py --strict
```

Expected: PASS.

**Step 3: Commit**

```bash
git add src/infrastructure/daemon_paths.py src/platform/daemon_manager.py tests/unit/test_daemon_manager.py
git commit -m "chore: clean daemon lifecycle hygiene"
```

---

### Task 4: Backfill `LSPClient.start()` failure-path tests if still cheap after daemon fixes

**Files:**
- Modify: `tests/unit/test_lsp_client_strict.py` or create `tests/unit/test_lsp_client_start.py`
- Modify only if needed: `src/infrastructure/lsp_client.py`

**Step 1: Write the failing tests**

Cover the currently untested failure paths:

```python
def test_start_sets_failed_when_binary_missing(...):
    ...


def test_start_sets_failed_when_popen_raises(...):
    ...
```

Mock `shutil.which`, `subprocess.Popen`, and telemetry hooks as needed.

**Step 2: Run test to verify current behavior**

Run:
```bash
uv run pytest tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py -v
```

Expected: Either new tests fail (if behavior is broken) or pass immediately, confirming the report item was coverage-only.

**Step 3: Implement only if tests reveal a real defect**

If tests expose missing state transitions or telemetry behavior, patch the smallest viable change in `src/infrastructure/lsp_client.py`. If the tests pass as written, keep this task as test-only.

**Step 4: Re-run the focused suite**

Run:
```bash
uv run pytest tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py tests/unit/daemon/test_runner_repo_root.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py tests/unit/daemon/test_runner_repo_root.py src/infrastructure/lsp_client.py
git commit -m "test: cover lsp client startup failures"
```

---

## Final Verification Gate

Run the full focused gate after all selected tasks:

```bash
uv run pytest \
  tests/unit/test_daemon_manager.py \
  tests/integration/daemon/test_daemon_manager.py \
  tests/unit/test_lsp_client_strict.py \
  tests/unit/test_lsp_ready_contract.py \
  tests/unit/daemon/test_runner_repo_root.py -v

uv run mypy \
  src/platform/daemon_manager.py \
  src/infrastructure/lsp_client.py \
  src/infrastructure/daemon_paths.py --strict

uv run ruff check \
  src/platform/daemon_manager.py \
  src/infrastructure/lsp_client.py \
  src/infrastructure/daemon_paths.py \
  tests/unit/test_daemon_manager.py \
  tests/unit/test_lsp_client_strict.py \
  tests/unit/test_lsp_ready_contract.py \
  tests/unit/daemon/test_runner_repo_root.py
```

## Risks / Watchouts

- `trifecta ctx validate --segment .` currently fails in this fresh worktree because the segment metadata files are not scaffolded for the worktree suffix (`agent_codex-lsp-daemon-review-remediation.md`, `prime_codex-lsp-daemon-review-remediation.md`), and `_ctx/` contains multiple `session_*.md` variants. Treat Trifecta search/get as useful but not authoritative validation inside this worktree until metadata is normalized.
- The review report file is present in the primary tree but not committed into this worktree. Use the primary-tree copy only as read-only review input; do not treat it as proof that the worktree already contains the report artifact.
- `src/infrastructure/lsp_daemon.py` is marked reference-only, so do not let hygiene changes there delay lifecycle fixes in the official daemon surface.
- Keep commits small: start lifecycle hardening, stop cleanup contract, then optional LSP client tests.

## Recommended Execution Order

1. Task 1 (`start()` lifecycle hardening)
2. Task 2 (`stop()` cleanup contract)
3. Task 3 (confirmed docstring hygiene)
4. Task 4 (optional LSP startup failure coverage)

