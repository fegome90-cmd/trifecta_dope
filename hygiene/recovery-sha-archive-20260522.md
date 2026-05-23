# SHA Recovery Archive — 2026-05-22

**Trigger**: git-hygiene-cleanup GC pruned 6 of 7 recovery SHAs recorded in spec. This audit recovers and preserves what was still fetchable from GitHub.

## SHAs Preserved as Archive Tags

| SHA (short) | Original Ref                             | Archive Tag                                          | Method                     |
| ----------- | ---------------------------------------- | ---------------------------------------------------- | -------------------------- |
| `d91a01ad`  | `codex/batch-2d-runtime-manager`         | `archive/branch-batch-2d-runtime-manager-20260522`   | PR #81 `refs/pull/81/head` |
| `15761042`  | `codex/wo-remediation-ci-baseline`       | `archive/branch-wo-remediation-ci-baseline-20260522` | PR #78 `refs/pull/78/head` |
| `3c594fa2`  | `fegome90-cmd/wo-0015-work`              | `archive/branch-wo-0015-work-20260522`               | PR #66 `refs/pull/66/head` |
| `15bf2a3d`  | tag `backup/wip-fulltext-fallback-audit` | `archive/tag-wip-fulltext-fallback-audit-20260522`   | `git fetch origin <sha>`   |

All tags are annotated with message: `Archive preserved SHA from git hygiene recovery audit 2026-05-22: <context>`.

All tags pushed to origin and verified via `git ls-remote --tags origin`.

## SHAs Already Preserved (No Action Needed)

| SHA (short) | Existing Preservation                         | Verification                             |
| ----------- | --------------------------------------------- | ---------------------------------------- |
| `c5d8e937`  | tag `archive/dirty-main-2025-01-06` on origin | `git rev-parse` confirms same commit     |
| `a8766aa9`  | ancestor of `main` and `origin/main`          | `git merge-base --is-ancestor` confirmed |

## SHAs Irrecuperable — ACCEPTED RESIDUAL RISK

### `c9fca10a` — `codex/wo-frictionless-closeout`

**Context**: Branch with no associated PR, deleted during git-hygiene-cleanup. GC pruned the local object.

**Recovery attempts**:

1. `git ls-remote origin refs/heads/codex/wo-frictionless-closeout` → empty (branch deleted)
2. `gh api repos/fegome90-cmd/trifecta_dope/git/commits/c9fca10a` → HTTP 404
3. `git fetch origin c9fca10a68c4f8a6e3d0b5f4c2a1e9d8b7f6e5a4` → `remote error: upload-pack: not our ref`
4. `gh pr list --state all --search "frictionless closeout"` → no matching PRs
5. `git ls-remote origin "refs/pull/*/head" | grep friction` → no matches
6. `git log --all --oneline --grep="frictionless"` → no matches
7. `gh api "repos/fegome90-cmd/trifecta_dope/git/refs" --paginate --jq '.[].ref' | grep friction` → no matches

**Assessment**: The commit object no longer exists on GitHub. This SHA is permanently lost. The branch contained work related to frictionless closeout of WorkOrders (based on `docs/plans/2026-03-18-wo-frictionless-closeout-plan.md` which references this work). The plan document is still in the repo and provides context for what the branch contained.

**Risk**: LOW. The branch was 9 weeks stale with no PR. No code from it was ever merged. The associated plan document survives in the repo.

## Actions Taken

- Created 4 annotated archive tags, pushed to origin
- Cleaned 3 temporary remote-tracking refs (`archive/pr-*`)
- Verified `archive/dirty-main-2025-01-06` already preserved — no duplication
- Verified `a8766aa9` reachable from main — no tag needed

## Actions NOT Taken

- Did not recreate any work branches
- Did not delete any tags or refs
- Did not merge or close any PRs
- Did not modify source code
- Did not run git gc

## Verification Commands

```bash
# Verify all archive tags on origin
git ls-remote --tags origin | grep archive

# Verify specific tag points to expected commit
git rev-parse archive/branch-batch-2d-runtime-manager-20260522^{commit}
# Expected: d91a01ad806e2544b35ec8c202d314549a1b139a
```
