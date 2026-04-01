## Stash Cleanup — Consolidated Findings (8 agents)

**Stashes:** 8 | **Completed:** 8/8

### 🗑 DROP (6)

- **stash@{0}** `codex/wo-remediation-merge-ready` — telemetry changes
  - Files: 2 | Risk: Bajo | Telemetry/temp metadata, fully regenerable
- **stash@{1}** `codex/wo-remediation-merge-ready` — On codex/wo-remediation-merge-ready: ci-baseline-lint-exploration
  - Files: 54 | Risk: Bajo | Lint cosmetics (54 files), branch merged via PR #71
- **stash@{2}** `codex/wo-remediation-plan` — On codex/wo-remediation-plan: remediation-nonmerge-artifacts
  - Files: 4 | Risk: Bajo | Non-merge artifacts from planning branch (4 files)
- **stash@{3}** `feat/search-pipeline-refactor` — telemetry files
  - Files: 2 | Risk: Bajo | Telemetry/temp metadata, fully regenerable
- **stash@{4}** `fix/wo-0055-code-review-issues` — On fix/wo-0055-code-review-issues: temp stash for WO-0015 finish
  - Files: 16 | Risk: Bajo | Temp stash for WO-0015 finish, branch merged 4x (PRs #56,#60,#61,#64)
- **stash@{6}** `feat/wo-WO-0015` — WO-0015 salvage before cleanup
  - Files: 5 | Risk: Bajo | WO-0015 completed, salvage no longer needed

### ⚠️ DROP_WITH_REVIEW (1)

- **stash@{5}** `fix/wo-0055-code-review-issues` — WIP on fix/wo-0055-code-review-issues: 034a376 fix(wo): canonicalize transition_to_failed cleanup + status (WO-0059)
  - Files: 105 | Risk: Medio-bajo | WIP 105 files, branch merged 4x. Large snapshot, verify key tests

### 📦 EXPORT_THEN_DROP (1)

- **stash@{7}** `feat/hn-benchmark-truth-mode` — main_branch_cleanup_20260219
  - Files: 5 | Risk: Medio | Branch merged (PR #55) but has improved benchmark data (GOLD queries, recall@k=1.0)
