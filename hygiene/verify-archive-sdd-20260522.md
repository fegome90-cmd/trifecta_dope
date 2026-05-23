# Verify + Archive SDD Report — 2026-05-22

## Conditions Verified

| #   | Condition                                           | Result  | Evidence                                                        |
| --- | --------------------------------------------------- | ------- | --------------------------------------------------------------- | ------------------------ |
| 1   | `main == origin/main`                               | ✅ PASS | Both at `b6a0b656` (pre-archive), then `fe6debe` (post-archive) |
| 2   | `stash-preserve-codex-freeze-v1` on origin          | ✅ PASS | `6d2660fb` at `refs/tags/stash-preserve-codex-freeze-v1`        |
| 3   | `origin/hygiene/stash-preserve-codex-freeze` exists | ✅ PASS | `07a8cf4d`                                                      |
| 4   | Dependabot PRs dynamic query                        | ✅ PASS | `gh pr list --state open --author "app/dependabot"` → `[]`      |
| 5   | No functional changes                               | ✅ PASS | `git diff --name-only origin/main..main                         | grep -E "^src/"` → empty |
| 6   | Subtask A report persistent                         | ✅ PASS | `hygiene/recovery-sha-archive-20260522.md`                      |
| 7   | Subtask B report persistent                         | ✅ PASS | `hygiene/precommit-ctx-sync-analysis-20260522.md`               |

## Archive Executed

Both SDD changes archived as completed:

- `openspec/changes/archive/2026-05-22-publish-main-backlog/` — 5 files (4 SDD + archive-report)
- `openspec/changes/archive/2026-05-22-git-hygiene-cleanup/` — 5 files (4 SDD + archive-report)

Active change directories removed from `openspec/changes/`.

## Residual Follow-ups Registered

| Follow-up                                  | Priority | Origin                                                  |
| ------------------------------------------ | -------- | ------------------------------------------------------- |
| `precommit-ctx-sync-fix`                   | Medium   | Subtask B — hook regex causes dirty loop                |
| `ctx-generated-artifacts-gitignore-policy` | Low      | Subtask B — evaluate runtime artifact tracking          |
| `recovery-sha-preservation-audit`          | Low      | Subtask A — 1 SHA permanently lost                      |
| `dependency-mypy-floor-update`             | Low      | git-hygiene-cleanup — re-trigger Dependabot for pyright |
| `dependency-typer-gap-assessment`          | Low      | git-hygiene-cleanup — evaluate Typer version gap        |

## Notable Observation

The archive commit (`fe6debe`) did NOT trigger the ctx sync hook — confirming Subtask B analysis. Only `_ctx/*` changes trigger sync; `hygiene/*` and `openspec/*` do not.
