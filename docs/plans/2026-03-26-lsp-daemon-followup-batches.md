# LSP Daemon Follow-up Batches Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the remaining LSP daemon backlog through small reviewable batches, with multiple commits on `codex/lsp-daemon-review-remediation`, then open a final PR, merge, and return to `main`.

**Architecture:** Keep fixes incremental and evidence-driven. Batch the remaining work by operational surface: (1) daemon lifecycle hardening still inside `DaemonManager`, (2) `LSPClient` lifecycle and readiness semantics, (3) parity/hygiene items around adjacent adapters, and (4) larger or riskier contract drift only if the earlier batches stay small and green. Do not let legacy/MVP cleanup expand the PR unnecessarily.

**Tech Stack:** Python 3.12+, pytest, mypy --strict, ruff, uv, git worktrees, Trifecta CLI.

---

## Scope Triage

### Recommended before PR
- `_acquire_singleton_lock()` startup/stale-lock race
- post-`SIGKILL` verification only probes once
- `lsp_client.stop()` leaves references alive
- semantic drift of `health_check_responds`
- possible truthiness parity issue in `src/infrastructure/lsp_daemon.py`

### Only if earlier batches stay cheap and green
- larger `runtime_manager.py` contract drift

### Defer / no-go for this PR unless active usage proves otherwise
- `src/application/lsp_manager.py` legacy/MVP surface

Rationale:
- The first five items are still close to current operational behavior and likely fit into reviewable bugfix commits.
- `runtime_manager.py` drift is broader contract alignment work and should not delay the PR unless the change stays surgical.
- `lsp_manager.py` looks like legacy/MVP cleanup and is the easiest place for scope creep.

---

### Task 1: Harden daemon-manager shutdown and lock semantics

**Files:**
- Modify: `src/platform/daemon_manager.py`
- Test: `tests/unit/test_daemon_manager.py`
- Test: `tests/integration/daemon/test_daemon_manager_integration.py`

**Batch intent:** Finish the two remaining daemon-manager lifecycle debts in one commit:
1. stale-lock / startup-in-progress race in `_acquire_singleton_lock()`
2. one-shot post-`SIGKILL` probe in `stop()`

**Step 1: Write failing tests**

Add focused regressions for:

```python
def test_acquire_singleton_lock_does_not_clean_live_startup_lock(...):
    ...


def test_stop_retries_post_sigkill_until_process_is_gone(...):
    ...
```

The lock test should simulate a bind failure where another startup legitimately owns the lock but has not yet published pid/socket. The stop test should simulate a process that is still visible on the first post-`SIGKILL` probe and disappears only after a short retry window.

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_daemon_manager.py -k "startup_lock or post_sigkill" -v
```

Expected: FAIL because the current code still treats some startup windows as stale and only probes once after `SIGKILL`.

**Step 3: Write minimal implementation**

Implement the narrowest viable fix:
- strengthen `_acquire_singleton_lock()` so it does not reap a lock that may belong to a valid in-progress startup
- replace the one-shot post-`SIGKILL` check with a short bounded retry loop

Avoid larger redesigns (lock ownership protocol, PID metadata formats, etc.).

**Step 4: Run focused verification**

Run:
```bash
uv run pytest tests/unit/test_daemon_manager.py tests/integration/daemon/test_daemon_manager_integration.py -q
uvx ruff check src/platform/daemon_manager.py tests/unit/test_daemon_manager.py tests/integration/daemon/test_daemon_manager_integration.py
uv run mypy src/platform/daemon_manager.py --strict
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/platform/daemon_manager.py tests/unit/test_daemon_manager.py tests/integration/daemon/test_daemon_manager_integration.py
git commit -m "fix(daemon-manager): harden lock and shutdown verification"
```

---

### Task 2: Clean up `LSPClient.stop()` lifecycle residue

**Files:**
- Modify: `src/infrastructure/lsp_client.py`
- Test: `tests/unit/test_lsp_client_strict.py`
- Reference: `tests/unit/test_lsp_ready_contract.py`

**Batch intent:** Make `stop()` leave the client in a truly closed/reset state by clearing stale process/thread/request references.

**Step 1: Write failing tests**

Add minimal regressions such as:

```python
def test_stop_clears_process_and_thread_references(...):
    ...


def test_stop_clears_pending_request_tracking(...):
    ...
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_lsp_client_strict.py -k "clears_process or pending_request" -v
```

Expected: FAIL because `stop()` currently transitions state but keeps internal references alive.

**Step 3: Write minimal implementation**

Update `stop()` to clear only the proven residual state needed for single-shot safety and clean restart behavior:
- `process`
- `_thread`
- pending request bookkeeping / thread-safe maps if still populated

Do not redesign the whole client lifecycle in this batch.

**Step 4: Run focused verification**

Run:
```bash
uv run pytest tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py -q
uvx ruff check src/infrastructure/lsp_client.py tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py
uv run mypy src/infrastructure/lsp_client.py --strict
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/infrastructure/lsp_client.py tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py
git commit -m "fix(lsp-client): clear lifecycle residue on stop"
```

---

### Task 3: Align readiness semantics and daemon adapter parity

**Files:**
- Modify: `src/infrastructure/lsp_client.py`
- Modify: `docs/contracts/LSP_READY_INVARIANTS.md`
- Modify: `src/infrastructure/lsp_daemon.py`
- Test: `tests/unit/test_lsp_ready_contract.py`
- Test: daemon-adjacent tests only if needed

**Batch intent:** Resolve the semantic drift around `health_check_responds` and bring `lsp_daemon.py` truthiness handling into parity with the already-fixed handler path.

**Step 1: Write/adjust failing tests**

Add or tighten tests for two things:

```python
def test_ready_invariant_matches_actual_handshake_behavior(...):
    ...


def test_lsp_daemon_treats_empty_dict_as_valid_response(...):
    ...
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_lsp_ready_contract.py -v
```

And, if there is a focused daemon adapter test path, run that targeted test too.

Expected: FAIL or contract/doc mismatch evidence showing the invariant name/meaning is off and `lsp_daemon.py` still uses raw truthiness.

**Step 3: Write minimal implementation**

Choose the smallest truthful alignment:
- either rename/redefine `health_check_responds` semantics to match what the code actually verifies
- or strengthen the code if a real round-trip health check is already intended and cheap to add
- update `lsp_daemon.py` truthiness check to use `is not None` parity if the audit finding still holds

Do not turn this batch into a full LSP protocol redesign.

**Step 4: Run focused verification**

Run:
```bash
uv run pytest tests/unit/test_lsp_ready_contract.py tests/unit/test_lsp_client_strict.py -q
uvx ruff check src/infrastructure/lsp_client.py src/infrastructure/lsp_daemon.py docs/contracts/LSP_READY_INVARIANTS.md tests/unit/test_lsp_ready_contract.py tests/unit/test_lsp_client_strict.py
uv run mypy src/infrastructure/lsp_client.py src/infrastructure/lsp_daemon.py --strict
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/infrastructure/lsp_client.py src/infrastructure/lsp_daemon.py docs/contracts/LSP_READY_INVARIANTS.md tests/unit/test_lsp_ready_contract.py tests/unit/test_lsp_client_strict.py
git commit -m "fix(lsp): align readiness semantics and adapter parity"
```

---

### Task 4: Evaluate `runtime_manager.py` drift as a scoped contract cleanup

**Files:**
- Modify: `src/platform/runtime_manager.py`
- Reference: `src/platform/daemon_manager.py`
- Test: create/update only if a real runtime contract test exists or is cheap to add

**Batch intent:** Decide whether `runtime_manager.py` can be corrected as a small contract cleanup or should be left deferred.

**Step 1: Investigate before coding**

Check current usage:
```bash
rg -n "RuntimeManager|DaemonRuntime" src tests
```

Expected outcome:
- If the protocols are effectively unused or documentation-only drift, either shrink the cleanup to comments/types or defer.
- If active consumers rely on them, proceed with a small truthful alignment.

**Step 2: If cheap, write the failing contract test or assertion**

Only add a test if you can define a crisp contract without opening a refactor spiral.

**Step 3: Apply minimal alignment or explicitly defer**

Options in priority order:
1. cheap doc/type correction only
2. limited protocol alignment if active consumers are narrow
3. defer if it becomes architectural

**Step 4: Verify**

Run only the exact impacted tests plus:
```bash
uvx ruff check src/platform/runtime_manager.py
uv run mypy src/platform/runtime_manager.py --strict
```

**Step 5: Commit or skip**

If implemented:
```bash
git add src/platform/runtime_manager.py <tests-if-any>
git commit -m "refactor(runtime): align daemon runtime contract"
```

If not implemented, record explicit defer in session notes / PR description instead of forcing a weak patch.

---

### Task 5: Explicitly defer `lsp_manager.py` legacy/MVP cleanup unless usage proves it belongs in this PR

**Files:**
- Reference only: `src/application/lsp_manager.py`

**Batch intent:** Avoid accidental scope creep.

**Step 1: Check real usage**

Run:
```bash
rg -n "lsp_manager|LSPManager" src tests
```

**Step 2: Decide**

- If usage is inactive/legacy: do **not** patch in this PR. Mention defer in PR notes.
- If active usage is unexpectedly high and the defect is blocking: create a separate plan or a new branch after this PR, not inside the current micro-batch flow.

No commit expected from this task unless evidence proves it became mandatory.

---

## Final Pre-PR Verification Gate

After completing the recommended pre-PR batches (Tasks 1-3, and optionally Task 4 if it stays small), run:

```bash
uv run pytest \
  tests/unit/test_daemon_manager.py \
  tests/integration/daemon/test_daemon_manager_integration.py \
  tests/unit/daemon/test_lsp_handler.py \
  tests/unit/test_daemon_use_case.py \
  tests/unit/test_lsp_client_strict.py \
  tests/unit/test_lsp_ready_contract.py \
  tests/unit/daemon/test_runner_repo_root.py -q

uvx ruff check \
  src/platform/daemon_manager.py \
  src/infrastructure/daemon/lsp_handler.py \
  src/infrastructure/lsp_client.py \
  src/infrastructure/lsp_daemon.py \
  src/application/daemon_use_case.py \
  src/platform/runtime_manager.py \
  src/infrastructure/daemon_paths.py \
  tests/unit/test_daemon_manager.py \
  tests/integration/daemon/test_daemon_manager_integration.py \
  tests/unit/daemon/test_lsp_handler.py \
  tests/unit/test_daemon_use_case.py \
  tests/unit/test_lsp_client_strict.py \
  tests/unit/test_lsp_ready_contract.py \
  tests/unit/daemon/test_runner_repo_root.py

uv run mypy \
  src/platform/daemon_manager.py \
  src/infrastructure/daemon/lsp_handler.py \
  src/infrastructure/lsp_client.py \
  src/infrastructure/lsp_daemon.py \
  src/application/daemon_use_case.py \
  src/platform/runtime_manager.py \
  src/infrastructure/daemon_paths.py --strict
```

Expected: all pass.

---

## PR / Merge / Return-to-main Closeout

### After the final approved batch commit

**Step 1: Push branch**
```bash
git push -u origin codex/lsp-daemon-review-remediation
```

**Step 2: Open PR**

Create one PR that clearly lists:
- anchor commit already landed: `7640291`
- follow-up batch commits included
- items explicitly deferred:
  - `lsp_manager.py` legacy/MVP cleanup (unless unexpectedly required)
  - any `runtime_manager.py` work that proves architectural

**Step 3: Final review pass**
- request code review
- address only validated review items
- keep batch boundaries visible in the PR description

**Step 4: Merge**
- merge only after the final verification gate is fresh and green

**Step 5: Return to `main` and clean worktree**
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
git checkout main
git pull --ff-only
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/codex-lsp-daemon-review-remediation
git status --short
git worktree remove ../.worktrees/codex-lsp-daemon-review-remediation
```

Adjust cleanup only if you intentionally keep the worktree for post-merge validation.

---

## Recommended Execution Order

1. Task 1 — daemon-manager lock/shutdown hardening
2. Task 2 — `LSPClient.stop()` lifecycle cleanup
3. Task 3 — readiness semantics + adapter parity
4. Task 4 — `runtime_manager.py` only if it remains surgical
5. Task 5 — explicit defer / no-go for `lsp_manager.py`

## Suggested Commit Series Before PR

1. `fix(daemon-manager): harden lock and shutdown verification`
2. `fix(lsp-client): clear lifecycle residue on stop`
3. `fix(lsp): align readiness semantics and adapter parity`
4. Optional: `refactor(runtime): align daemon runtime contract`
5. PR open / merge / return to `main`
