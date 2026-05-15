# Remote Publication Verification

**Date**: 2026-05-15
**Scope**: Verify that the git hygiene cycle is fully materialized on GitHub remote.

---

## Commits Pushed

23 commits pushed: `49031bd2..809a64f4` → `origin/main`

All commits are documentation/policy/config. No functional code changes.

## Files Changed in 23 Commits

| Category | Files | Expected |
|----------|-------|----------|
| hygiene/ docs | 27 files (authority, memos, policies, corrections, reports) | ✅ |
| .github/dependabot.yml | Tightened config (HIGH patch-only) | ✅ |
| HISTORY.md + session log | Traceability | ✅ |
| _ctx/ | Context pack, generated stubs, telemetry | ✅ (auto-generated) |
| .gitignore + .mailmap | Phase 2 cleanup | ✅ |
| docs/plans/ | Stale plan note | ✅ |
| pyproject.toml | Plotly removed, tree-sitter floors updated (Phase 5) | ✅ |
| uv.lock | Regenerated after pyproject.toml edit | ✅ (automatic) |
| src/, scripts/, tests/ | **NONE** | ✅ No functional changes |

## Verification Results

| Check | Result |
|-------|--------|
| `main == origin/main` | ✅ Both → `809a64f4` |
| Tag `stash-preserve-codex-freeze-v1` on remote | ✅ `6d2660fb` |
| Branch `origin/hygiene/stash-preserve-codex-freeze` exists | ✅ `07a8cf4d` |
| Tag SHA == Branch SHA | ✅ Both `07a8cf4d` |
| PR #104 (actions/dependency-review-action 4→5) | OPEN — not touched |
| PR #105 (pyright 1.1.408→1.1.409) | CLOSED by GitHub after push |
| Stash local (`stash@{0}` on `49031bd2`) | Present — not dropped |

## Note on PR #105

PR #105 (pyright patch) was auto-closed by GitHub after our push. This likely happened because the new dependabot config changed the grouping or limits, causing Dependabot to re-evaluate and close the stale PR. No manual action taken.

## Residual State

- **1 open PR**: #104 (actions major — needs manual review per policy)
- **1 stale stash entry**: `stash@{0}` from `49031bd2` — content should be covered by `stash-preserve-codex-freeze-v1` tag but not verified commit-by-commit
- **4 PRESERVED/REVIEW branches**: untouched, pending human decision
- **Remote tracking ref pruned**: `origin/dependabot/pip/dev-dependencies-883de9310f` deleted by `git fetch --prune` (PR #105 closed)

## Confirmation

- ✅ Truth local = truth remote
- ✅ No unexpected functional changes pushed
- ✅ No stash dropped
- ✅ No PRs merged or closed by us
- ✅ Tag + branch both exist on remote, same SHA
- ✅ Git hygiene cycle fully materialized on GitHub
