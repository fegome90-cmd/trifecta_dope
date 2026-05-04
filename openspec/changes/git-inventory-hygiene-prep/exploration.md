# Exploration: Git Inventory for Hygiene Prep

> **Change**: `git-inventory-hygiene-prep`
> **Phase**: explore
> **Date**: 2026-05-03
> **Agent**: sdd-explore (glm-5.1)
> **Mode**: hybrid (engram + openspec)

---

## Current State

Trifecta Dope is a Python 3.12+ CLI tool with **949 total commits** across all branches and **633 commits on main**. The repo is a single-developer project with heavy AI-assisted development (478 commits from "Felipe Gonzalez Meriño" via local Mac, plus 168 from "Checkpointer", 156 from GitHub-linked identity, 106 from Gmail identity). The branching model is **feature-branch with WO (Work Order) naming convention** — no strict gitflow, but branches follow patterns like `feat/wo-*`, `codex/*`, `fix/*`, `job/*`, and `dependabot/*`.

**Key metric**: 31 remote branches exist, but only **4 are fully merged into main**. The remaining 27 are unmerged — 10 are dependabot dependency update branches with open PRs, 5 have closed PRs with unmerged commits (HIGH risk), 3 are squash-merged (MEDIUM risk), and the rest are stale feature/fix branches between 3 weeks and 3+ months old.

There is **1 local stash** containing a large batch of uncommitted work (22 files, ~123K line changes) from a codex freeze operation. There are **3 tags** — all safety/archive snapshots, not version releases. **No submodules**, **no LFS** configured.

---

## Branches

### Local Branches
| Branch | Last Commit | Status |
|--------|------------|--------|
| `main` | 8 days ago (86739d27) | Active, HEAD |

Only 1 local branch exists. Good.

### Remote Branches — Merged into main (5)
| Branch | Notes |
|--------|-------|
| `origin/main` | Primary branch |
| `origin/feat/documentation-skill-phase1` | Merged, stale — safe to delete |
| `origin/fegome90-cmd/wo-skills-system` | Merged, stale — safe to delete |
| `origin/job/WO-0042` | Merged, stale — safe to delete |
| `origin/job/WO-0052` | Merged, stale — safe to delete |

### Remote Branches — NOT merged (21)
| Branch | Age | Category | Risk | Action |
|--------|-----|----------|------|--------|
| `origin/codex/skill-hub-ssot-rebuild` | 3 weeks | codex | Low — PR #103 merged | **Delete** |
| `origin/dependabot/pip/pandas-gte-3.0.2` | 3 weeks | dependabot | PR #102 open | Review/merge/close |
| `origin/dependabot/pip/pytest-env-gte-1.6.0` | 3 weeks | dependabot | PR #101 open | Review/merge/close |
| `origin/dependabot/pip/plotly-gte-6.7.0` | 3 weeks | dependabot | PR #100 open | Review/merge/close |
| `origin/dependabot/pip/ruamel-yaml-gte-0.19.1` | 3 weeks | dependabot | PR #99 open | Review/merge/close |
| `origin/dependabot/pip/tree-sitter-gte-0.25.2` | 3 weeks | dependabot | PR #98 open | Review/merge/close |
| `origin/dependabot/pip/filelock-gte-3.25.2` | 3 weeks | dependabot | PR #97 open | Review/merge/close |
| `origin/dependabot/pip/mypy-gte-1.20.1` | 3 weeks | dependabot | PR #96 open | Review/merge/close |
| `origin/dependabot/pip/types-pyyaml-gte-6.0.12.20260408` | 3 weeks | dependabot | PR #95 open | Review/merge/close |
| `origin/dependabot/pip/safety-gte-3.7.0` | 3 weeks | dependabot | PR #94 open | Review/merge/close |
| `origin/dependabot/pip/typer-gte-0.24.1` | 3 weeks | dependabot | PR #93 open | Review/merge/close |
| `origin/codex/skill-hub-authority-anchor-closeout` | 3 weeks | codex | PR #86 merged | **Delete** |
| `origin/copilot-pull-request-reviewer/audit-github-history` | 4 weeks | copilot | PR #85 draft | Review/close |
| `origin/fix/search-context-preview-truncation` | 5 weeks | fix | PR #83 closed | **Investigate** — 36 unmerged commits |
| `origin/codex/batch-2d-runtime-manager` | 5 weeks | codex | PR #81 closed | **Investigate** — 38 unmerged commits |
| `origin/codex/docs-skillhub-context-refresh-20260327` | 5 weeks | codex | PR #80 closed | **Investigate** — 33 unmerged commits |
| `origin/codex/graph-mvp` | 6 weeks | codex | PR #74 merged | **Delete** |
| `origin/codex/wo-frictionless-closeout` | 6 weeks | codex | No PR | Investigate/delete |
| `origin/codex/wo-remediation-ci-baseline` | 7 weeks | codex | PR #78 closed | **Investigate** — 12 unmerged commits |
| `origin/feat/e-v1-daemon-run` | 8 weeks | feat | No PR | Investigate/delete |
| `origin/feat/skills-contracts-explain` | 8 weeks | feat | PR #68 closed | **Investigate** — 14 unmerged commits |
| `origin/feat/wo-WO-0042` | 3+ months | feat | No PR | Investigate/delete |
| `origin/feat/wo-WO-0044` | 3+ months | feat | No PR | Investigate/delete |
| `origin/feat/wo-WO-0047` | ~3 months | feat | No PR | Investigate/delete |
| `origin/fegome90-cmd/wo-0015-work` | 10 weeks | feat | No PR | Investigate/delete |
| `origin/fix/wo-0055-code-review-issues` | 10 weeks | fix | No PR | Investigate/delete |

**Summary**: 4 branches can be safely deleted (fully merged into main). 3 squash-merged branches need caution (code in main, commit history not). 5 closed-PR branches have unmerged commits — HIGH risk, require developer confirmation. 10 dependabot branches need review. 7 orphan branches need investigation.

### Stale Local Branch Config Entries
The `.git/config` contains tracking entries for **9 local branches that no longer exist locally**:
- `feat/wo-WO-0011`
- `codex/chore-wo-hygiene`
- `codex/ci-main-unblock`
- `codex/wo-hygiene-rebase`
- `codex/wo-guard-wave1`
- `codex/wo-take-immediate-validation`
- `codex/chore-wo-hygiene-safe`
- `codex/merge-trifecta-wo-sidecar-hardening`
- `codex/main-consolidation`

These are ghost tracking refs — the branches were deleted locally but their config entries remain.

---

## Tags

| Tag | Type | Target | Date | Purpose |
|-----|------|--------|------|---------|
| `archive/dirty-main-2025-01-06` | lightweight (commit) | c5d8e937 | 2026-01-06 | Archive of dirty main state |
| `backup/wip-fulltext-fallback-audit` | lightweight (commit) | 15bf2a3d | 2026-01-03 | Backup before search changes |
| `pre-merge-WO-0045-20260213-202041` | annotated (tag) | f795f044 | 2026-02-13 | Safety snapshot before WO-0045 merge |

**Assessment**: 3 tags, all safety/archive. No versioning tags (no v0.x, v1.x). This is expected for an active development phase. Tags are not stale — they serve a purpose.

---

## Remotes

| Remote | URL | Type |
|--------|-----|------|
| `origin` | `https://github.com/fegome90-cmd/trifecta_dope.git` | HTTPS |

Single remote, standard configuration. Fetch/push both point to same URL. No issues.

---

## Worktrees

| Path | Commit | Branch |
|------|--------|--------|
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope` | 86739d27 | main |

Only the main worktree. No linked worktrees active. Clean state.

---

## Stashes

| Stash | Branch | Description | Files | Size |
|-------|--------|-------------|-------|------|
| `stash@{0}` | main | `codex-pre-sh003-freeze-nonsh003` | 22 files | ~123K line diff |

**Risk**: This is a MASSIVE stash containing uncommitted work from a codex freeze operation. Includes telemetry data, session logs, reconcile patches (240K+ lines), and actual code changes (skill-hub runtime, skill manifest, CLI, tests). If this stash is dropped accidentally, significant work is lost.

**Recommendation**: Either (1) apply and commit to a branch, or (2) document explicitly that it's intentionally frozen.

---

## Hooks

### Active Hook: `.git/hooks/pre-commit`
- **Purpose**: Auto-sync context pack when `_ctx/*.md` files change
- **Behavior**: Runs `uv run trifecta ctx sync --segment .` and stages `_ctx/context_pack.json`
- **Custom hooks path**: `core.hookspath=scripts/hooks` is configured but the active pre-commit is in `.git/hooks/`

### Custom Hooks Directory: `scripts/hooks/`
Contains 11 hook scripts:
| File | Purpose |
|------|---------|
| `commit-msg` | Commit message validation |
| `common.sh` | Shared utilities |
| `install-hooks.sh` | Hook installer |
| `pre_commit_test_gate.sh` | Test gate before commit |
| `pre-commit` | Pre-commit checks (alternative) |
| `prevent_manual_wo_closure.sh` | WO closure guard |
| `run-doc-skill.sh` | Doc skill runner |
| `test_prevent_manual_wo_closure.sh` | Tests for WO closure guard |
| `trifecta_integrity_check.py` | Integrity validation |
| `wo_fmt_lint.sh` | WO format/lint checks |

**Assessment**: The `core.hookspath` config points to `scripts/hooks/` but `.git/hooks/pre-commit` is the one that's active. There may be a disconnect between the configured path and actual hook execution. This needs investigation — `core.hookspath` should override `.git/hooks/`.

---

## Git Config

### Local `.git/config` Observations
- **`core.hookspath=scripts/hooks`**: Custom hooks directory — BUT `.git/hooks/pre-commit` also exists and is the standard Git hooks location. Potential conflict.
- **No local user.name/user.email**: Falls back to global config (`Felipe Gonzalez` / `felipe.gonzalez@users.noreply.github.com`)
- **9 ghost branch tracking entries**: Local branches deleted but config entries remain

### Author Identity Fragmentation (CRITICAL)
The same person commits under **3 different identities**:
1. `Felipe Gonzalez Meriño <felipe_gonzalez@MacBook-Pro-de-Felipe.local>` — 478 commits (local Mac)
2. `Felipe Gonzalez <felipe.gonzalez@users.noreply.github.com>` — 156 commits (GitHub noreply)
3. `Felipe <fegome.90@gmail.com>` — 106 commits (Gmail)

Plus bot identities: Checkpointer (168), dependabot (19), copilot-swe-agent (13), coderabbitai (2), Claude (4), Codex (1), Copilot (1).

**Risk**: Commit history attribution is fragmented. GitHub's contribution graph may not unify these. A `.mailmap` file would resolve this.

---

## Gitignore

Comprehensive `.gitignore` covering:
- Python bytecode (`__pycache__/`, `*.pyc`)
- Virtual environments (`.venv/`, `venv/`)
- IDE files (`.idea/`, `.vscode/`)
- Build artifacts (`dist/`, `build/`, `*.egg-info/`)
- Trifecta runtime state (`.trifecta/`, `_ctx/telemetry/`, `_ctx/generated/`)
- Worktrees (`.worktrees/`)
- Agent state (`.claude/context_memory/`, `.atl/`, `.fork/`)
- Development tools (`.sidecar/`, `.todos/`, `.pi/`)
- Special exemption: `!_ctx/logs/reconcile_real_testing.json`

**Assessment**: Well-maintained. No obvious issues.

---

## Submodules

None. Clean.

---

## LFS

Not configured. No large files tracked. Clean.

---

## Log Analysis

### Recent Activity (Last 30 days)
| Date | Commits |
|------|---------|
| 2026-04-20 | 8 |
| 2026-04-25 | 4 |
| 2026-04-24 | 4 |
| 2026-04-19 | 4 |
| 2026-04-16 | 1 |
| 2026-04-15 | 1 |
| 2026-04-12 | 1 |
| 2026-04-01 | 1 |

**Total April commits**: ~24. Moderate activity with a burst on April 19-20 (LSP/oracle work).

### Top Contributors
| Author | Commits | % |
|--------|---------|---|
| Felipe Gonzalez Meriño (MacBook) | 478 | 50.4% |
| Checkpointer (bot) | 168 | 17.7% |
| Felipe Gonzalez (GitHub) | 156 | 16.4% |
| Felipe (Gmail) | 106 | 11.2% |
| dependabot[bot] | 19 | 2.0% |
| copilot-swe-agent[bot] | 13 | 1.4% |
| Others | 9 | 0.9% |

### Branching Strategy
**Pattern**: Feature-branch with Work Order (WO) naming convention.
- `feat/wo-WO-XXXX` — Feature branches tied to work orders
- `codex/*` — Automated agent branches
- `fix/*` — Bug fix branches
- `job/WO-XXXX` — Job execution branches
- `dependabot/*` — Automated dependency updates
- `fegome90-cmd/*` — Direct user branches

No `develop` branch exists. No release branches. This is **trunk-based development with feature branches**, not gitflow.

---

## CI/CD

### GitHub Actions Workflows (3)

#### 1. CI (`ci.yml`)
- **Trigger**: Push/PR to `main` and `develop`
- **Jobs**: `test` (unit + integration + acceptance + coverage), `lint` (ruff + mypy + SSOT grep guard + WO lint + skill lint), `telemetry-health` (main only)
- **Python**: 3.12 via `uv`
- **Coverage**: Codecov upload
- **Custom guards**: SSOT Grep Guard (prevents deprecated segment ID usage), WO format/lint check

#### 2. Security Scan (`security-scan.yml`)
- **Trigger**: Push/PR to `main`/`develop` + weekly Monday 09:00 UTC
- **Jobs**: CodeQL, dependency review (PR only), Bandit, Safety, TruffleHog secret scanning
- **Note**: `continue-on-error: true` on CodeQL and dependency-review — failures won't block CI

#### 3. WO Weekly Gate (`wo-weekly-gate.yml`)
- **Trigger**: Weekly Monday 06:00 UTC + manual
- **Purpose**: Work Order system health check, audit, GC
- **Artifacts**: 90-day retention for reports

**Assessment**: Solid CI/CD setup. Minor concern: `continue-on-error` on security scans means they could silently fail.

---

## Open PRs/Issues

### Open PRs (11)
| # | Title | Author | Age | Category |
|---|-------|--------|-----|----------|
| 102 | pandas >=3.0.2 | dependabot | 3 weeks | deps |
| 101 | pytest-env >=1.6.0 | dependabot | 3 weeks | deps |
| 100 | plotly >=6.7.0 | dependabot | 3 weeks | deps |
| 99 | ruamel-yaml >=0.19.1 | dependabot | 3 weeks | deps |
| 98 | tree-sitter >=0.25.2 | dependabot | 3 weeks | deps |
| 97 | filelock >=3.25.2 | dependabot | 3 weeks | deps |
| 96 | mypy >=1.20.1 | dependabot | 3 weeks | deps |
| 95 | types-pyyaml >=6.0.12.20260408 | dependabot | 3 weeks | deps |
| 94 | safety >=3.7.0 | dependabot | 3 weeks | deps |
| 93 | typer >=0.24.1 | dependabot | 3 weeks | deps |
| 85 | [WIP] Analyze GitHub PR sequence | copilot-reviewer | 4 weeks | draft |

**10 dependabot PRs pending review.** All 3 weeks old. The typer 0.24.1 update (PR #93) is notable as a major version bump for the CLI framework.

### Open Issues (6)
| # | Title | Label | Date |
|---|-------|-------|------|
| 91 | fix(cli-ast): LSP daemon client uses non-operational authority module | — | 2026-04-12 |
| 92 | fix(skill-hub): runtime promotion wrapper dependency detection | — | 2026-04-12 |
| 90 | fix(lsp): unreachable FAILED branch in lsp_handler | — | 2026-04-12 |
| 89 | fix(daemon): stale-lock fallback reopens double-start race | — | 2026-04-12 |
| 88 | fix(skill-hub): segment_id config lookup inconsistent with SSOT | — | 2026-04-12 |
| 87 | fix(skill-hub): segment-root containment for manifest paths | — | 2026-04-12 |

All 6 issues opened on 2026-04-12. 2 relate to daemon, 3 to skill-hub, 1 to LSP. No labels assigned beyond defaults.

### Closed Issues (1)
- #70: WO-M0 incomplete: daemon run command not implemented (bug) — closed 2026-03-06

---

## Risks

1. **Author identity fragmentation (HIGH)**: 3 different author identities for the same person (740 total commits split across them). This affects `git blame`, `git shortlog`, GitHub contribution graphs, and any tooling that relies on author identity. Without a `.mailmap`, the history is permanently fragmented.

2. **Stash bomb (MEDIUM)**: The single stash (`stash@{0}`) contains 123K+ lines of changes including reconcile patches. Accidental `git stash drop` or `git stash clear` would lose this. It's been sitting there unstated.

3. **Stale remote branches (MEDIUM)**: 8 branches that are merged or have closed PRs still exist on remote, creating noise. 6+ branches with no associated PR need investigation before deletion.

4. **Ghost branch config entries (LOW)**: 9 local branch tracking entries in `.git/config` for branches that no longer exist locally. This is harmless but clutters the config.

5. **Hook path disconnect (LOW)**: `core.hookspath=scripts/hooks` is configured, but `.git/hooks/pre-commit` also exists. Git should use `scripts/hooks/` as the hooks path, meaning `.git/hooks/pre-commit` may not be executing. This needs verification.

6. **Dependabot PR staleness (MEDIUM)**: 10 dependabot PRs have been open for 3 weeks. These may have merge conflicts by now, and security updates (safety >=3.7.0) should be prioritized.

7. **No CODEOWNERS (LOW)**: No `.github/CODEOWNERS` file exists. For a single-developer project this is fine, but it means all PR reviews are manual.

8. **Security scan continue-on-error (LOW)**: CodeQL and dependency review have `continue-on-error: true`, meaning security findings won't block CI. Intentional but worth noting.

9. **No versioning tags (INFO)**: No `v*` tags exist. The project has no release versioning via tags. Not a risk for development, but relevant for release management.

---

## Hygiene Recommendations (preliminary)

### Priority 1 — Immediate (Low risk, high value)
1. **Create `.mailmap`** to unify author identities
2. **Delete 4 fully-merged remote branches** (feat/documentation-skill-phase1, fegome90-cmd/wo-skills-system, job/WO-0042, job/WO-0052)
3. **Clean 9 ghost branch tracking entries** from `.git/config`

### Priority 2 — Short-term (Needs investigation)
4. **Caution with 3 squash-merged branches** — code is in main but commit history not preserved (codex/skill-hub-ssot-rebuild, codex/skill-hub-authority-anchor-closeout, codex/graph-mvp)
5. **Investigate 5 closed-PR branches with unmerged commits** — code is NOT in main, developer must confirm disposal (fix/search-context-preview-truncation, codex/batch-2d-runtime-manager, codex/docs-skillhub-context-refresh-20260327, codex/wo-remediation-ci-baseline, feat/skills-contracts-explain)
6. **Review and triage 10 dependabot PRs** — merge or close
7. **Investigate 7 orphan branches with no PR** — determine if work should be preserved or abandoned
8. **Resolve stash@{0}** — apply to a named branch or document as intentionally frozen (NO drop)
9. **Verify hook execution path** — confirm whether `scripts/hooks/` or `.git/hooks/` is active

### Priority 3 — Improvements
10. **Add labels to open issues** — all 6 issues lack classification labels
11. **Close or convert PR #85** (copilot WIP draft, 4 weeks old)
12. **Document CI/CD `continue-on-error`** as accepted risk or review recommendation
13. **Document versioning tag absence** as accepted or create strategy
14. **Consider `CODEOWNERS`** if the project scales beyond single developer

### Not recommended
- Deleting tags (all serve archival purpose)
- Changing branching strategy (current model works)
- Modifying CI/CD pipelines (well-configured)

---

## Ready for Proposal

**Yes** — the inventory is complete. The next step is a proposal (`sdd-propose`) defining the scope of the hygiene phase, specifically which of the above recommendations to include, in what order, and with what rollback strategy.

**Key decision needed from user**: What to do with stash@{0} (preserve on a branch or drop?) and how aggressive to be with branch deletion.
