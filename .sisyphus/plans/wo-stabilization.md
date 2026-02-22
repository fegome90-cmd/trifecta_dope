# WO System Stabilization Plan

**Created:** 2026-02-21
**Status:** READY TO EXECUTE
**Source:** Ops Gap Audit 2026-02-21 + Forensic Analysis
**Timeline:** 30 days (P0: 7 days, P1: 14 days, P2: 30 days)

---

## Objective

Restore **operational integrity** of the WO system and eliminate commit blocks, with measurable "fail-closed" criteria.

### Definition of Done (Global)

- [ ] `trifecta_integrity_check.py` **exit 0** on clean repo
- [ ] `wo_audit.py --fail-on split_brain,running_without_lock,ghost_worktree,zombie_worktree` **exit 0**
- [ ] Pre-commit allows commits without bypass
- [ ] Session markers "intent" auto-generated on take (≥80% on new WOs)

---

## Current State (Baseline)

### Snapshot (2026-02-21)

| Metric | Value | Status |
|--------|-------|--------|
| Worktrees active | 14 (1 main + 13 WO) | ⚠️ |
| WO YAMLs total | 60 | - |
| Locks active | 3 (WO-0015, WO-0055, WO-0057) | - |
| Split-brain WOs | 5 (WO-0014, 0015, 0046, 0048, 0055) | 🔴 P0 |
| Ghost worktrees | 1 (WO-0052) | 🔴 P0 |
| Zombie worktrees | 8 (estimate) | 🟡 P1 |
| Pre-commit status | EXIT 1 (blocking commits) | 🔴 P0 |
| Session markers adoption | 5.8% | 🟡 P1 |

### Root Cause Analysis

| GAP | Description | Root Cause |
|-----|-------------|------------|
| GAP-01 | Zombies accumulate | `finish_wo_transaction` has NO `git worktree remove` |
| GAP-02 | Commits blocked | Split-brain detected by integrity check |
| GAP-03 | 5 split-brain WOs | Process crash / SIGKILL / partial rollback |
| GAP-04 | Ghost WO-0052 | WO completed without YAML state update |

---

## Phase 0 — Baseline Freeze (Day 0)

**Goal:** Capture reproducible state before modifications.

### Tasks

- [ ] **T0.1** Save snapshot to `data/wo_forensics_baseline/`
  ```bash
  mkdir -p data/wo_forensics_baseline
  git rev-parse HEAD > data/wo_forensics_baseline/head.txt
  git rev-parse --abbrev-ref HEAD > data/wo_forensics_baseline/branch.txt
  git worktree list --porcelain > data/wo_forensics_baseline/worktrees.txt
  ls -la _ctx/jobs/{pending,running,done,failed} > data/wo_forensics_baseline/jobs_inventory.txt
  ```
- [ ] **T0.2** Run full audit and save JSON
  ```bash
  uv run python scripts/wo_audit.py --out data/wo_forensics_baseline/wo_audit.json
  ```
- [ ] **T0.3** Run integrity check and capture output
  ```bash
  python3 scripts/hooks/trifecta_integrity_check.py 2>&1 | tee data/wo_forensics_baseline/integrity_check.txt
  ```

### QA Scenarios

- Baseline is reproducible with saved commands and outputs.

### Success Criteria

- [ ] All baseline files exist and contain expected data.

---

## Phase 1 — P0 Unblock (Day 1-3)

**Goal:** Eliminate split-brain and commit blocks.

### 1.1 Reconcile Split-Brain + Missing Locks

**Script:** `scripts/ctx_reconcile_state.py`

| Flag | Purpose |
|------|---------|
| `--apply` | Apply safe fixes |
| `--force` | Allow unsafe fixes |
| `--json PATH` | Write JSON report |

#### Tasks

- [ ] **T1.1** Run reconcile in dry-run mode
  ```bash
  uv run python scripts/ctx_reconcile_state.py --json data/wo_forensics_baseline/reconcile_plan.json
  ```
- [ ] **T1.2** Review plan JSON for each affected WO
- [ ] **T1.3** Apply safe fixes
  ```bash
  uv run python scripts/ctx_reconcile_state.py --apply --json data/wo_forensics_baseline/reconcile_result.json
  ```
- [ ] **T1.4** Verify split-brain WOs resolved
  - WO-0014: pending → done (final state)
  - WO-0015: pending+running → single state
  - WO-0046: running+failed → failed
  - WO-0048: running+failed → failed
  - WO-0055: pending+running → single state
- [ ] **T1.5** Verify no `running` without lock

#### QA Scenarios

| Scenario | Test |
|----------|------|
| Negative case | Introduce WO duplicate in sandbox, verify reconcile detects it |
| Real case | Confirm 5 split-brain WOs are in single state |

#### Success Criteria

- [ ] `python3 scripts/hooks/trifecta_integrity_check.py` exits 0
- [ ] `wo_audit.py --fail-on split_brain` exits 0

---

## Phase 2 — P0/P1 Cleanup (Day 3-7)

**Goal:** Remove ghost and zombie worktrees.

### 2.1 Remove Ghost Worktree (WO-0052)

**Evidence:** WO-0052 worktree exists, but no YAML in any state.

#### Tasks

- [ ] **T2.1** Confirm ghost status
  ```bash
  git worktree list --porcelain | grep -A3 WO-0052
  find _ctx/jobs -name "WO-0052*"  # Should return nothing
  ```
- [ ] **T2.2** Remove worktree
  ```bash
  git worktree remove /Users/felipe_gonzalez/Developer/agent_h/.worktrees/WO-0052
  ```
- [ ] **T2.3** Log before/after to `data/wo_forensics_baseline/ghost_cleanup.txt`

#### QA Scenarios

- [ ] WO-0052 no longer appears in `git worktree list`

#### Success Criteria

- [ ] `ghost_worktree` count = 0 in audit

### 2.2 Remove Zombie Worktrees

**Definition:** Worktree exists, but WO is in done/failed state.

#### Tasks

- [ ] **T2.4** Enumerate zombies
  ```bash
  uv run python scripts/wo_audit.py --out data/wo_forensics_baseline/zombie_inventory.json
  # Extract zombie_worktree findings
  ```
- [ ] **T2.5** For each zombie, remove worktree
  ```bash
  # Check if worktree is clean before removal
  git -C /path/to/worktree status --porcelain
  git worktree remove /path/to/worktree  # Use --force only if dirty and approved
  ```
- [ ] **T2.6** Log all removals to `data/wo_forensics_baseline/zombie_cleanup.txt`

#### QA Scenarios

- [ ] Audit reports 0 zombie worktrees

#### Success Criteria

- [ ] `zombie_worktree` count = 0 in audit

---

## Phase 3 — Recurrence Prevention (Day 7-14)

**Goal:** Hardened gates and cleanup automation.

### 3.1 Integrate `wo_audit.py` into Pre-Commit

**Current gap:** `trifecta_integrity_check.py` only checks split-brain and locks.

#### Tasks

- [ ] **T3.1** Create wrapper script or extend pre-commit config
  ```yaml
  # .pre-commit-config.yaml addition
  - id: wo-audit-gate
    name: WO Audit Gate
    entry: python scripts/wo_audit.py --fail-on split_brain,running_without_lock,ghost_worktree,zombie_worktree --out /tmp/wo_audit_gate.json
    language: system
    files: ^(_ctx/jobs/|\.worktrees/)
  ```
- [ ] **T3.2** Ensure error message is actionable (mentions WO IDs)
- [ ] **T3.3** Test with negative cases

#### QA Scenarios

| Case | Expected |
|------|----------|
| Commit with split-brain WO | Hook fails with explanation |
| Commit with running without lock | Hook fails with explanation |
| Commit with clean state | Hook passes |

#### Success Criteria

- [ ] 0 false-positive blocks in 1 week
- [ ] Bypass rate does not increase

### 3.2 Cut the Source: Cleanup on Close OR GC

**Decision required:**

| Option | Pros | Cons |
|--------|------|------|
| A: Add `git worktree remove` in `finish_wo_transaction` | Immediate, no extra scripts | Destructive in transaction, complex rollback |
| B: Create `ctx_wo_gc.py` (RECOMMENDED) | Idempotent, safe, observable | Requires scheduling |

#### Tasks (Option B - GC Script)

- [ ] **T3.4** Create `scripts/ctx_wo_gc.py`
  ```python
  # Features:
  # --dry-run: Report only
  # --apply: Execute cleanup
  # --force: Clean dirty worktrees (dangerous)
  # Output: JSON report of actions taken
  ```
- [ ] **T3.5** Implement zombie detection
- [ ] **T3.6** Implement ghost detection
- [ ] **T3.7** Implement stale lock cleanup
- [ ] **T3.8** Add tests in `tests/unit/test_ctx_wo_gc.py`
- [ ] **T3.9** Schedule weekly CI job (dry-run fails on issues)

#### QA Scenarios

- [ ] GC dry-run reports issues
- [ ] GC apply cleans issues
- [ ] GC respects dirty worktrees (no destruction without --force)

#### Success Criteria

- [ ] No new zombies created in 7 days of operation

---

## Phase 4 — Automated Evidence (Day 14-30)

**Goal:** Eliminate manual marker burden.

### 4.1 Auto-Intent Marker in `ctx_wo_take.py`

#### Tasks

- [ ] **T4.1** Modify `ctx_wo_take.py` to append marker on take
  ```python
  # After successful take, append to session log:
  # [WO-XXXX] intent: <brief description from WO YAML>
  ```
- [ ] **T4.2** Maintain stable format
- [ ] **T4.3** Add unit test for marker generation

#### QA Scenarios

- [ ] Take a WO → grep finds marker in session log

#### Success Criteria

- [ ] ≥80% of new WOs have intent marker (weekly measurement)

### 4.2 Auto-Result Marker in `ctx_wo_finish.py` (Optional)

#### Tasks

- [ ] **T4.4** On finish, generate `[WO-XXXX] result:` based on verdict
- [ ] **T4.5** Track `--skip-verification` usage (create metric if needed)

#### Success Criteria

- [ ] `--skip-verification` is exception, not norm

---

## Resources Required

| Resource | Role |
|----------|------|
| WO System Engineer | Implementation (all phases) |
| Repo Owner | Policy decisions (cleanup, force, bypass) |
| Daily time | 30-90 min for 7 days (pairing + review) |

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Delete worktree with uncommitted changes | Data loss | Dirty check + dry-run + require --force flag |
| Hard gates without repair | More bypasses | Sequence: reconcile/cleanup first, then gates |
| Markers remain manual | Low adoption | Auto-append in take, then finish |
| Reconcile breaks something | State corruption | Dry-run review + backup + rollback plan |

---

## Weekly KPIs

| KPI | Target | Source |
|-----|--------|--------|
| `split_brain` count | 0 | `wo_audit.py` |
| `running_without_lock` count | 0 | `wo_audit.py` |
| `ghost_worktree` count | 0 | `wo_audit.py` |
| `zombie_worktree` count | 0 | `wo_audit.py` |
| Intent marker adoption | ≥80% | grep session logs |
| Bypass events | 0 (trending down) | telemetry events |

---

## Execution Priority

**EXECUTE TODAY:**

1. **Phase 0** - Baseline freeze (15 min)
2. **Phase 1.1** - Reconcile dry-run + review (30 min)
3. **Phase 1.1** - Reconcile apply (15 min)
4. **Phase 2.1** - Ghost WO-0052 cleanup (10 min)

**Without these, everything else is makeup.**

---

## Commands Reference

```bash
# Baseline
uv run python scripts/wo_audit.py --out data/wo_forensics_baseline/wo_audit.json

# Reconcile
uv run python scripts/ctx_reconcile_state.py --json data/reconcile_plan.json
uv run python scripts/ctx_reconcile_state.py --apply --json data/reconcile_result.json

# Integrity check
python3 scripts/hooks/trifecta_integrity_check.py

# Worktree management
git worktree list --porcelain
git worktree remove .worktrees/WO-XXXX

# Audit gate
uv run python scripts/wo_audit.py --fail-on split_brain,running_without_lock,ghost_worktree,zombie_worktree --out /tmp/gate.json
```

---

## Next Session Handoff

When resuming this plan, run:

```bash
cat .sisyphus/plans/wo-stabilization.md
uv run python scripts/wo_audit.py --out data/wo_current_state.json
```

Then continue from the first unchecked task.

---

**Plan Version:** 1.0
**Last Updated:** 2026-02-21
