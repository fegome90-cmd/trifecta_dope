# Phase 3 — Working Tree Stabilization Audit

> **Date**: 2026-05-04
> **Baseline**: `main` at `86739d27` (origin/main)
> **Auditor**: SDD Apply Executor
> **Stash-preserve branch**: `origin/hygiene/stash-preserve-codex-freeze` at `07a8cf4d`

## Task 1: Baseline Verification

| Check | Result |
|-------|--------|
| `git fetch --all --prune --tags` | Clean, no new refs |
| `git status --short` on `main` | `?? hygiene/` (single untracked directory) |
| `origin/main` HEAD | `86739d27f5f0f44ec4a6c63363d1894ac5439d2b` |
| `origin/hygiene/stash-preserve-codex-freeze` | `07a8cf4d chore: preserve codex freeze stash content as branch` |
| `stash@{0}` | Present — `On main: codex-pre-sh003-freeze-nonsh003` |

**Conclusion**: Working tree is clean except for the `hygiene/` directory. Zero tracked modifications.

---

## Task 3: Working Tree Classification

### Complete File Listing

| File/Path | Type | Size | Classification | Reasoning |
|-----------|------|------|----------------|-----------|
| `hygiene/stash-20260504.patch` | Binary-like (diff patch) | 105.5 MB | **A) Stash/codex freeze** | This is the `git stash show -p` export from Phase 1. Content already preserved in `origin/hygiene/stash-preserve-codex-freeze` branch (309 files). Also confirmed the stash itself (`stash@{0}`) still exists intact. |

### Classification Summary

| Category | Count | Files |
|----------|-------|-------|
| A) Stash/codex freeze — already preserved | 1 | `hygiene/stash-20260504.patch` |
| B) Hygiene audit — should be on audit branch | 0 | (all hygiene docs already committed on audit branch) |
| C) Active legitimate work | 0 | (working tree has zero tracked modifications) |
| D) Generated artifact / local trash | 0 | (patch is classified A, not D — it's a preservation artifact) |
| E) Unknown | 0 | (nothing ambiguous found) |

---

## Task 4: Stash-Preserve Branch Comparison

### Verification: Does the branch contain everything from the stash?

| Metric | Stash-preserve branch | Stash@{0} |
|--------|----------------------|-----------|
| Files changed vs main | 309 | 255 |
| Insertions | 188,682 | 6074 (effective) |
| Deletions | 132,761 | 42,566 (effective) |

**Key findings**:
- The stash-preserve branch was created from a FULL working tree snapshot (including staged + unstaged + untracked), not just the stash diff.
- The stash-preserve branch contains 309 files changed — it is a **superset** of the stash content (255 files).
- The stash-preserve branch is preserved on remote: `origin/hygiene/stash-preserve-codex-freeze`.
- The stash itself (`stash@{0}`) remains intact.
- The local patch file (`hygiene/stash-20260504.patch`, 105.5 MB) is a redundant copy that cannot be pushed to GitHub (exceeds 100 MB limit).

**Verdict**: ✅ No work is at risk of loss. All stash content is preserved in TWO redundant locations:
1. `stash@{0}` — original git stash ref
2. `origin/hygiene/stash-preserve-codex-freeze` — remote branch (superset)

---

## Task 5: Recommendations

### Files Safe to Reset/Clean

| File | Action | Reasoning |
|------|--------|-----------|
| `hygiene/stash-20260504.patch` | **DELETE from local `main`** | Content is preserved in stash-preserve branch AND stash@{0}. This is a 105.5 MB local-only file that cannot be pushed. Removing it from `main`'s working tree restores a clean state. |
| `hygiene/` directory | **DELETE entirely** | Only contains the patch file above. Directory is not tracked on `main`. |

### Files That Should Be Committed

None. All hygiene documentation is already committed on `hygiene/git-audit-20260504` branch:
- `hygiene/branch-audit-20260504.md`
- `hygiene/ghost-*.txt` (before/after/backup/plan)
- `hygiene/post-audit-execution-20260504.md`
- `hygiene/preflight-20260504.md`
- `hygiene/sha-registry-20260504.md`
- `hygiene/stash-audit-20260504.md`
- `hygiene/summary-20260504.md`
- `hygiene/phase-2-closeout-20260504.md` (this session)
- `hygiene/phase-3-working-tree-stabilization-20260504.md` (this file)

### Files That Should Move to a New Branch

None needed. All artifacts are on the audit branch.

### Files That Should Be Added to .gitignore

| Pattern | Reasoning |
|---------|-----------|
| `hygiene/*.patch` | Prevents accidental staging of large patch files in future audits |

### Files Requiring Human Decision

None. The situation is straightforward:
- 1 untracked file (patch) → safe to delete (redundant with remote branch)
- 0 tracked modifications → clean working tree

### Verification: Stash-Preserve Branch Integrity

```
origin/hygiene/stash-preserve-codex-freeze
├── Commit: 07a8cf4d
├── Message: "chore: preserve codex freeze stash content as branch"
├── Files: 309 changed (superset of stash)
├── Status: Pushed to remote ✅
└── Contains: All staged + unstaged + untracked from freeze point
```

---

## Residual Items After Phase 3

1. **Patch file cleanup**: The 105.5 MB `hygiene/stash-20260504.patch` should be deleted from `main`'s working tree once the user confirms they're satisfied with the branch-based preservation.
2. **.gitignore entry**: Consider adding `hygiene/*.patch` to prevent future large patch accidents.
3. **Large repo artifacts**: The closeout document notes `_ctx/handoff/WO-0005/diff.patch` (57.9 MB) and `tests/fixtures/.../reconcile.patch` (83.26 MB) — these are separate from this audit and should be tracked for future cleanup.
4. **Stash@{0} remains**: MUST NOT be dropped. It is the third redundant copy of the preserved content.
