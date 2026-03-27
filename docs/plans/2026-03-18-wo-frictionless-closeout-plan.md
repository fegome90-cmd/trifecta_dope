# WO Frictionless Closeout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make a full WO lifecycle pass cleanly end-to-end without zombie worktrees, ambiguous post-close state, or topology-specific finish failures.

**Architecture:** Keep `state_root` and `execution_root` as separate contracts all the way through `take`, `finish`, audit, and cleanup. After a successful `finish`, introduce one explicit closeout policy that either removes the official WO worktree or rehomes it into a non-WO preserved baseline with an auditable decision artifact. The authoritative WO YAML stays immutable in meaning; the new behavior lives in post-finish closeout and in audit/GC visibility.

**Tech Stack:** Python 3.12, `uv`, git worktrees, pytest, Trifecta WO scripts, YAML-backed `_ctx` state.

---

### Task 0: Reconcile the Closeout Contract Before Coding

**Files:**
- Modify: `docs/plans/2026-03-18-wo-frictionless-closeout-plan.md`
- Reference: `docs/backlog/WORKFLOW.md`
- Reference: `docs/backlog/MANUAL_WO.md`

**Step 1: Read the plan once only for contradictions**

Check these exact invariants before touching code:
- `finish` has exactly one successful post-verify outcome: destroy the official WO path or rehome it to a non-WO preserved path
- failed verification means no closeout side effect runs
- `wo_audit.py`, `ctx_wo_gc.py`, docs, and tests all use the same meaning for “official WO worktree”
- merge status is explicit evidence for closeout policy, not a replacement for the authoritative `done` state

**Step 2: Record the contradiction review directly in the plan**

Append one short note under “Execution Notes” when implementation starts:
- `contract review: no contradictions found`
or
- `contract review: contradictions fixed before Task 1`

**Step 3: Fix plan contradictions before code if any are found**

Only adjust this plan if one task contradicts another on:
- when cleanup runs
- when preservation runs
- when audit should still report zombie state
- what evidence a successful finish must leave behind

**Step 4: Re-read Task 2, Task 3, Task 4, and Task 6**

Expected: the same closeout policy is described in all four places with no conflicting wording.

**Step 5: Commit the plan-only correction if needed**

```bash
git add docs/plans/2026-03-18-wo-frictionless-closeout-plan.md
git commit -m "docs: reconcile frictionless closeout contract before implementation"
```

### Task 1: Lock the Frictionless Closeout Contract in Tests

**Files:**
- Modify: `tests/integration/test_wo_closure.py`
- Modify: `tests/unit/test_ctx_wo_finish.py`
- Modify: `tests/unit/test_wo_finish_validators.py`
- Modify: `tests/unit/test_ctx_wo_gc.py`

**Step 1: Write the failing integration test for a successful closeout**

Add one scenario to `tests/integration/test_wo_closure.py` that proves:
- `ctx_wo_finish.py` succeeds from the supported sibling topology
- the authoritative WO state ends in `done`
- the official `.../.worktrees/WO-XXXX` path is not left alive
- a preserved baseline path is used only when the policy says to preserve

**Step 2: Run the integration test to verify it fails**

Run:
```bash
uv run pytest -q tests/integration/test_wo_closure.py -k frictionless
```

Expected: FAIL because today there is no single tested contract for post-finish closeout.

**Step 3: Write the failing unit tests for policy decisions**

Add unit tests that assert:
- merge status is classified explicitly, not inferred from WO `done`
- `finish` chooses one of two outcomes: `cleanup_official_worktree` or `preserve_baseline_checkout`
- GC no longer treats an intentionally rehomed non-WO baseline path as a WO zombie
- the selected closeout action produces explicit evidence fields instead of only implicit side effects

**Step 4: Run the unit slice to verify it fails**

Run:
```bash
uv run pytest -q tests/unit/test_ctx_wo_finish.py tests/unit/test_wo_finish_validators.py tests/unit/test_ctx_wo_gc.py -k "closeout or preserve or merge or zombie"
```

Expected: FAIL with missing helpers / missing policy behavior.

**Step 5: Commit the red tests**

```bash
git add tests/integration/test_wo_closure.py tests/unit/test_ctx_wo_finish.py tests/unit/test_wo_finish_validators.py tests/unit/test_ctx_wo_gc.py
git commit -m "test: lock frictionless WO closeout contract"
```

### Task 2: Add Explicit Closeout Policy and Merge Inspection

**Files:**
- Modify: `scripts/ctx_wo_finish.py`
- Modify: `scripts/helpers.py`
- Modify: `scripts/paths.py`
- Modify: `tests/unit/test_ctx_wo_finish.py`
- Modify: `tests/unit/test_paths.py`

**Step 1: Add failing unit coverage for exact helper names**

Target helpers to add and test:
- `detect_merge_status(...)`
- `resolve_closeout_policy(...)`
- `get_preserved_worktree_path(...)`

The tests must assert exact outcomes for:
- merged branch
- unmerged branch
- unsupported topology
- already-rehomed baseline path

**Step 2: Run the helper tests to verify they fail**

Run:
```bash
uv run pytest -q tests/unit/test_ctx_wo_finish.py tests/unit/test_paths.py -k "detect_merge_status or resolve_closeout_policy or preserved_worktree_path"
```

Expected: FAIL because the helpers do not exist yet.

**Step 3: Implement the minimal helper layer**

Implement in `scripts/helpers.py` and `scripts/paths.py`:
- exact merge-target check against explicit refs
- deterministic non-WO preserved path generation
- no reuse of `.../.worktrees/WO-XXXX` once a WO is `done`

Wire `scripts/ctx_wo_finish.py` to compute the post-finish action only after verification passes.
Also define one closeout evidence payload with at least:
- checked refs for merge detection
- resolved merge status
- chosen closeout action
- official WO path before closeout
- preserved path after closeout when applicable

**Step 4: Run the helper tests to verify they pass**

Run:
```bash
uv run pytest -q tests/unit/test_ctx_wo_finish.py tests/unit/test_paths.py -k "detect_merge_status or resolve_closeout_policy or preserved_worktree_path"
```

Expected: PASS

**Step 5: Commit the helper layer**

```bash
git add scripts/ctx_wo_finish.py scripts/helpers.py scripts/paths.py tests/unit/test_ctx_wo_finish.py tests/unit/test_paths.py
git commit -m "feat: add explicit WO closeout policy and merge inspection"
```

### Task 3: Rehome or Clean the Official WO Worktree During Finish

**Files:**
- Modify: `scripts/ctx_wo_finish.py`
- Modify: `scripts/helpers.py`
- Modify: `scripts/ctx_wo_gc.py`
- Modify: `tests/integration/test_wo_crash_safety.py`
- Modify: `tests/unit/test_ctx_wo_gc.py`

**Step 1: Add the failing tests for the actual side effect**

Cover two exact outcomes:
- clean merged branch -> official WO worktree is removed
- unmerged but preserve-worthy branch -> official WO worktree is moved to a non-WO preserved path and optionally locked

Also add one negative test:
- failed verification -> no closeout side effect runs

**Step 2: Run the affected tests to verify they fail**

Run:
```bash
uv run pytest -q tests/integration/test_wo_crash_safety.py tests/unit/test_ctx_wo_gc.py -k "closeout or preserve or remove or move"
```

Expected: FAIL because finish/GC are not coordinated around preserved baselines.

**Step 3: Implement the post-finish closeout**

In `scripts/ctx_wo_finish.py`:
- keep state transition logic authoritative
- only after successful finish, execute one closeout action
- emit deterministic paths and no manual YAML rewrites

In `scripts/ctx_wo_gc.py`:
- keep WO-named paths as GC scope
- ignore intentionally rehomed non-WO preserved paths

**Step 4: Run the closeout tests to verify they pass**

Run:
```bash
uv run pytest -q tests/integration/test_wo_crash_safety.py tests/unit/test_ctx_wo_gc.py -k "closeout or preserve or remove or move"
```

Expected: PASS

**Step 5: Commit the side-effect layer**

```bash
git add scripts/ctx_wo_finish.py scripts/helpers.py scripts/ctx_wo_gc.py tests/integration/test_wo_crash_safety.py tests/unit/test_ctx_wo_gc.py
git commit -m "feat: rehome or clean official WO worktree after finish"
```

### Task 4: Make Audit and Evidence Tell the Truth

**Files:**
- Modify: `scripts/wo_audit.py`
- Modify: `scripts/ctx_wo_finish.py`
- Modify: `docs/backlog/WORKFLOW.md`
- Modify: `docs/backlog/MANUAL_WO.md`
- Modify: `tests/unit/test_wo_audit_fail_but_running.py`

**Step 1: Add failing audit tests**

Add tests that prove:
- a preserved non-WO baseline is not reported as `zombie_worktree`
- a `done` WO still mounted at `.../.worktrees/WO-XXXX` is reported as zombie
- finish writes a decision/evidence artifact when it preserves instead of destroys
- finish writes enough closeout evidence to explain the destroy path too, not only the preserve path

**Step 2: Run the audit slice to verify it fails**

Run:
```bash
uv run pytest -q tests/unit/test_wo_audit_fail_but_running.py -k "zombie or preserved or baseline"
```

Expected: FAIL because audit only understands WO-named live paths, not the preserved-closeout contract.

**Step 3: Implement the audit/evidence update**

In `scripts/wo_audit.py`:
- keep the current invariant on WO-named paths
- make preserved non-WO baselines invisible to zombie classification

In `scripts/ctx_wo_finish.py`:
- emit a small `decision.md` or equivalent closeout artifact when preservation is chosen
- emit one structured closeout record for every successful finish, with the exact merge refs checked and the exact action taken

Update `docs/backlog/WORKFLOW.md` and `docs/backlog/MANUAL_WO.md` so operators know:
- when finish destroys
- when finish preserves
- where the preserved baseline lives
- why the official WO path must disappear after `done`
- what evidence files to inspect first when a closeout outcome looks wrong

**Step 4: Run the audit slice to verify it passes**

Run:
```bash
uv run pytest -q tests/unit/test_wo_audit_fail_but_running.py -k "zombie or preserved or baseline"
```

Expected: PASS

**Step 5: Commit the audit/docs update**

```bash
git add scripts/wo_audit.py scripts/ctx_wo_finish.py docs/backlog/WORKFLOW.md docs/backlog/MANUAL_WO.md tests/unit/test_wo_audit_fail_but_running.py
git commit -m "fix: align audit and docs with WO closeout policy"
```

### Task 5: Add One Full Happy-Path Regression for “WO Without Friction”

**Files:**
- Create: `tests/integration/test_wo_frictionless_lifecycle.py`
- Modify: `tests/integration/test_wo_closure.py`
- Modify: `tests/unit/test_ctx_wo_take.py`

**Step 1: Write the failing end-to-end regression**

Create `tests/integration/test_wo_frictionless_lifecycle.py` with one scenario that:
- bootstraps a WO
- preflights it
- takes it into a worktree
- simulates work + commit
- finishes it successfully
- verifies there is no official WO zombie
- verifies merge/closeout outcome is explicit

**Step 2: Run the full regression to verify it fails**

Run:
```bash
uv run pytest -q tests/integration/test_wo_frictionless_lifecycle.py tests/integration/test_wo_closure.py tests/unit/test_ctx_wo_take.py -k "frictionless or lifecycle"
```

Expected: FAIL until the new closeout contract is fully wired.

**Step 3: Implement the minimal missing glue**

Only fix what the new full-path regression proves is still missing.
Do not broaden scope into grandfathering, pending semantics, or unrelated WO cleanup.

**Step 4: Run the regression and the WO gate slice**

Run:
```bash
uv run pytest -q tests/integration/test_wo_frictionless_lifecycle.py tests/integration/test_wo_closure.py tests/integration/test_wo_crash_safety.py tests/unit/test_ctx_wo_finish.py tests/unit/test_ctx_wo_take.py tests/unit/test_ctx_wo_gc.py tests/unit/test_wo_audit_fail_but_running.py tests/unit/test_wo_finish_validators.py
```

Expected: PASS

Then run:
```bash
uv run python scripts/ctx_backlog_validate.py --strict
uv run python scripts/wo_audit.py --out /tmp/wo_audit_post_frictionless.json
```

Expected:
- backlog validate PASS
- audit shows no new P0/P1 introduced by the test flow

**Step 5: Commit the full regression**

```bash
git add tests/integration/test_wo_frictionless_lifecycle.py tests/integration/test_wo_closure.py tests/unit/test_ctx_wo_take.py
git commit -m "test: add full frictionless WO lifecycle regression"
```

### Task 6: Final Verification and Operator Handoff

**Files:**
- Modify: `docs/backlog/WORKFLOW.md`
- Modify: `docs/backlog/MANUAL_WO.md`
- Modify: `docs/plans/2026-03-18-wo-frictionless-closeout-plan.md`

**Step 1: Run the focused verification pack**

Run:
```bash
make wo-lint
uv run pytest -q tests/integration/test_wo_frictionless_lifecycle.py tests/integration/test_wo_closure.py tests/integration/test_wo_crash_safety.py tests/unit/test_ctx_wo_finish.py tests/unit/test_ctx_wo_take.py tests/unit/test_ctx_wo_gc.py tests/unit/test_wo_audit_fail_but_running.py tests/unit/test_wo_finish_validators.py
uv run python scripts/ctx_backlog_validate.py --strict
uv run python scripts/wo_audit.py --out /tmp/wo_audit_post_frictionless.json
uv run python scripts/ctx_wo_gc.py --dry-run
```

**Step 2: Verify expected outputs**

Expected:
- test slice PASS
- backlog validate PASS
- audit does not report a fresh `zombie_worktree` for the completed WO
- GC dry-run does not propose deleting an official WO worktree that should have already been cleaned or rehomed by finish
- the closeout evidence clearly states `merge_status`, checked refs, chosen action, and resulting path

**Step 3: Update docs one final time**

Make sure both WO docs explicitly describe:
- supported topology
- finish closeout policy
- preserved baseline behavior
- operator rule: no live `done` WO under `.../.worktrees/WO-XXXX`
- exact closeout evidence checklist:
  - merge refs checked
  - merge status result
  - official WO path before action
  - closeout action executed
  - preserved path when applicable

**Step 4: Record execution notes in this plan**

Append a short “Execution Notes” section with:
- final commands run
- expected audit result
- known non-goals left out

**Step 5: Commit the handoff**

```bash
git add docs/backlog/WORKFLOW.md docs/backlog/MANUAL_WO.md docs/plans/2026-03-18-wo-frictionless-closeout-plan.md
git commit -m "docs: finalize frictionless WO closeout operator plan"
```

## Non-Goals

- Reopening grandfathering or pending normalization semantics
- Redesigning `wo_authority.py`
- Solving arbitrary historical zombie worktrees outside the new closeout contract
- Merging `feat/wo-WO-0061` as part of this change

## Success Criteria

- A WO can go `pending -> running -> done` in the supported topology without manual YAML moves.
- `ctx_wo_finish.py` leaves no official WO zombie behind.
- Merge status is explicit and auditable, not guessed from `done`.
- If preservation is needed, the checkout is rehomed to a non-WO path with evidence.
- Audit and GC agree with finish behavior.

## Recommended Execution Order

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
