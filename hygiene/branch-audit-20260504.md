# Branch Audit — 2026-05-04

> **STATUS: HISTORICAL AUDIT + RESOLUTION.**
> Original tables may contain stale branch names and the known pypy/pandas typo.
> Current branch fates are defined by "Resolution Status (Updated 2026-05-09)".

## Baseline
- **origin/main**: `86739d27f5f0f44ec4a6c63363d1894ac5439d2b`

---

## Section A: Fully Merged Branches

| # | Branch | Tip SHA | Is-Ancestor | Classification |
|---|--------|---------|-------------|----------------|
| 1 | `origin/feat/documentation-skill-phase1` | `c1cfaf030f8c542613f3769d743b32fbb1a0cb59` | YES (exit 0) | ✅ SAFE_DELETE_CANDIDATE |
| 2 | `origin/fegome90-cmd/wo-skills-system` | `b4c0645f86c9550628bdc99f41418157ca913160` | YES (exit 0) | ✅ SAFE_DELETE_CANDIDATE |
| 3 | `origin/job/WO-0042` | `7aa436732077e72c0beac1c79f5cc08bdab19e53` | YES (exit 0) | ✅ SAFE_DELETE_CANDIDATE |
| 4 | `origin/job/WO-0052` | `5e733e5bc80de085866901082c61c62378cc6375` | YES (exit 0) | ✅ SAFE_DELETE_CANDIDATE |

**Summary**: All 4 branches are fully merged ancestors of `origin/main`. All content is reachable from main. Safe to delete remote branches if desired.

---

## Section B: Squash-Merged Branches

| # | Branch | Tip SHA | Is-Ancestor | PR # | PR State | PR Merged At | Diff (excl gen) | Classification |
|---|--------|---------|-------------|------|----------|-------------|-----------------|----------------|
| 1 | `origin/codex/skill-hub-ssot-rebuild` | `796b5a5039766e5fd928ef533504c8ec98109e12` | NO (exit 1) | #103 | MERGED | 2026-04-15 | 127 files, +1068/-16068 | ✅ SAFE_ARCHIVE_CANDIDATE |
| 2 | `origin/codex/skill-hub-authority-anchor-closeout` | `abb02938d602f40c789809415e85d451cca092d6` | NO (exit 1) | #86 | MERGED | 2026-04-12 | 133 files, +1307/-17346 | ✅ SAFE_ARCHIVE_CANDIDATE |
| 3 | `origin/codex/graph-mvp` | `ef56233c275b4b0e0334a40777f0154b08b23d7a` | NO (exit 1) | #74 | MERGED | 2026-03-15 | 346 files, +2502/-39702 | ✅ SAFE_ARCHIVE_CANDIDATE |

**Analysis**: All 3 branches have MERGED PRs via squash-merge. The large diffs are caused by:
1. Squash-merge creates different commit SHAs than the branch commits
2. `origin/main` advanced significantly after the merges (new commits on top)
3. Branches contain pre-merge state that diverged from current main

**Cherry output**: All commits show `+` prefix (not equivalent to any main commit), confirming squash-merge was used.

**Verdict**: All content is in main via squash. Branches are safe to archive/delete.

---

## Section C: Closed-PR / Orphan Branches

### C.1: Merged PRs (Squash) — SAFE_ARCHIVE_CANDIDATE

| # | Branch | Tip SHA | Last Commit | Ahead | PR # | PR State | Diffstat | Classification |
|---|--------|---------|-------------|-------|------|----------|----------|----------------|
| 1 | `origin/feat/wo-WO-0042` | `f065927d` | 2026-02-15 | 1 | #42 | MERGED | 840 files | ✅ SAFE_ARCHIVE_CANDIDATE |
| 2 | `origin/feat/wo-WO-0044` | `e62b6a0b` | 2026-02-15 | 2 | #43 | MERGED | 839 files | ✅ SAFE_ARCHIVE_CANDIDATE |
| 3 | `origin/feat/wo-WO-0047` | `2fcc80cd` | 2026-02-15 | 1 | #41 | MERGED | 841 files | ✅ SAFE_ARCHIVE_CANDIDATE |
| 4 | `origin/fix/wo-0055-code-review-issues` | `7cb317c1` | 2026-02-23 | 4 | #64,#61,#60,#56 | ALL MERGED | 636 files | ✅ SAFE_ARCHIVE_CANDIDATE |

### C.2: Closed PRs (Not Merged) — DO_NOT_DELETE

| # | Branch | Tip SHA | Last Commit | Ahead | PR # | PR State | Diffstat | Classification |
|---|--------|---------|-------------|-------|------|----------|----------|----------------|
| 1 | `origin/codex/batch-2d-runtime-manager` | `d91a01ad` | 2026-03-29 | 38 | #81 | CLOSED | 340 files, +123k/-171k | 🚫 DO_NOT_DELETE |
| 2 | `origin/codex/docs-skillhub-context-refresh-20260327` | `82862131` | 2026-03-27 | 33 | #80 | CLOSED | 316 files, +122k/-169k | 🚫 DO_NOT_DELETE |
| 3 | `origin/codex/wo-remediation-ci-baseline` | `15761042` | 2026-03-15 | 12 | #78 | CLOSED | 441 files, +18k/-198k | 🚫 DO_NOT_DELETE |
| 4 | `origin/feat/skills-contracts-explain` | `3e15a215` | 2026-03-06 | 14 | #68 | CLOSED | 558 files, +17k/-213k | 🚫 DO_NOT_DELETE |
| 5 | `origin/fegome90-cmd/wo-0015-work` | `3c594fa2` | 2026-02-23 | 16 | #66 | CLOSED | 648 files, +14k/-223k | 🚫 DO_NOT_DELETE |
| 6 | `origin/fix/search-context-preview-truncation` | `9bd392ac` | 2026-03-30 | 36 | #83 | CLOSED | 290 files, +122k/-164k | 🚫 DO_NOT_DELETE |

### C.3: Open PRs — DO_NOT_DELETE

| # | Branch | Tip SHA | Last Commit | Ahead | PR # | PR State | Diffstat | Classification |
|---|--------|---------|-------------|-------|------|----------|----------|----------------|
| 1 | `origin/copilot-pull-request-reviewer/audit-github-history` | `2c25b0b7` | 2026-04-02 | 1 | #85 | OPEN | 297 files | 🚫 DO_NOT_DELETE |

### C.4: No PR Found — MANUAL_REVIEW

| # | Branch | Tip SHA | Last Commit | Ahead | Diffstat | Classification |
|---|--------|---------|-------------|-------|----------|----------------|
| 1 | `origin/codex/wo-frictionless-closeout` | `c9fca10a` | 2026-03-19 | 16 | 347 files, +123k/-175k | ⚠️ MANUAL_REVIEW |
| 2 | `origin/feat/e-v1-daemon-run` | `c7c63e3e` | 2026-03-06 | 1 | 528 files, +18k/-210k | ⚠️ MANUAL_REVIEW |

### C.5: Dependabot Branches (All Open PRs) — DO_NOT_DELETE

| # | Branch | Tip SHA | Last Commit | PR # | PR State | Classification |
|---|--------|---------|-------------|------|----------|----------------|
| 1 | `origin/dependabot/pip/filelock-gte-3.25.2` | `5a1d37cf` | 2026-04-13 | #97 | OPEN | 🚫 DO_NOT_DELETE |
| 2 | `origin/dependabot/pip/mypy-gte-1.20.1` | `6ec19136` | 2026-04-13 | #96 | OPEN | 🚫 DO_NOT_DELETE |
| 3 | `origin/dependabot/pip/pypy-gte-3.0.2` | `84fffe34` | 2026-04-13 | #102 | OPEN | 🚫 DO_NOT_DELETE |
| 4 | `origin/dependabot/pip/plotly-gte-6.7.0` | `19cf0fa3` | 2026-04-13 | #100 | OPEN | 🚫 DO_NOT_DELETE |
| 5 | `origin/dependabot/pip/pytest-env-gte-1.6.0` | `113c6ee6` | 2026-04-13 | #101 | OPEN | 🚫 DO_NOT_DELETE |
| 6 | `origin/dependabot/pip/ruamel-yaml-gte-0.19.1` | `45947618` | 2026-04-13 | #99 | OPEN | 🚫 DO_NOT_DELETE |
| 7 | `origin/dependabot/pip/safety-gte-3.7.0` | `7ea710c4` | 2026-04-13 | #94 | OPEN | 🚫 DO_NOT_DELETE |
| 8 | `origin/dependabot/pip/tree-sitter-gte-0.25.2` | `c1172a3e` | 2026-04-13 | #98 | OPEN | 🚫 DO_NOT_DELETE |
| 9 | `origin/dependabot/pip/typer-gte-0.24.1` | `b1a1be02` | 2026-04-13 | #93 | OPEN | 🚫 DO_NOT_DELETE |
| 10 | `origin/dependabot/pip/types-pyyaml-gte-6.0.12.20260408` | `a79c4d87` | 2026-04-13 | #95 | OPEN | 🚫 DO_NOT_DELETE |

---

## Resolution Status (Updated 2026-05-09)

### Section A: Fully Merged Branches — ALL DELETED

| # | Branch | Resolution | Date | Phase |
|---|--------|------------|------|-------|
| 1 | `origin/feat/documentation-skill-phase1` | ✅ DELETED | 2026-05-04 | Task 6 |
| 2 | `origin/fegome90-cmd/wo-skills-system` | ✅ DELETED | 2026-05-04 | Task 6 |
| 3 | `origin/job/WO-0042` | ✅ DELETED | 2026-05-04 | Task 6 |
| 4 | `origin/job/WO-0052` | ✅ DELETED | 2026-05-04 | Task 6 |

### Section B: Squash-Merged Branches — ALL DELETED

| # | Branch | Resolution | Date | Phase |
|---|--------|------------|------|-------|
| 1 | `origin/codex/skill-hub-ssot-rebuild` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |
| 2 | `origin/codex/skill-hub-authority-anchor-closeout` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |
| 3 | `origin/codex/graph-mvp` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |

### Section C.1: Merged PRs (Squash) — ALL DELETED

| # | Branch | Resolution | Date | Phase |
|---|--------|------------|------|-------|
| 1 | `origin/feat/wo-WO-0042` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |
| 2 | `origin/feat/wo-WO-0044` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |
| 3 | `origin/feat/wo-WO-0047` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |
| 4 | `origin/fix/wo-0055-code-review-issues` | ✅ DELETED | 2026-05-04 (orig) → 2026-05-06 (archive) | Task 7 + Phase 4 |

### Section C.2: Closed PRs (Not Merged) — Resolved in Phase 5

| # | Branch | Resolution | Date | Note |
|---|--------|------------|------|------|
| 1 | `origin/codex/batch-2d-runtime-manager` | 🔒 PRESERVED | 2026-05-09 | 38 unique commits, kept on remote |
| 2 | `origin/codex/docs-skillhub-context-refresh-20260327` | ✅ DELETED | 2026-05-09 | Phase 5 cleanup |
| 3 | `origin/codex/wo-remediation-ci-baseline` | 🔒 PRESERVED | 2026-05-09 | 12 unique commits, kept on remote |
| 4 | `origin/feat/skills-contracts-explain` | ✅ DELETED | 2026-05-09 | Phase 5 cleanup |
| 5 | `origin/fegome90-cmd/wo-0015-work` | 🔒 PRESERVED | 2026-05-09 | 16 unique commits, kept on remote |
| 6 | `origin/fix/search-context-preview-truncation` | ✅ DELETED | 2026-05-09 | Phase 5 cleanup |

### Section C.3: Open PRs — Resolved

| # | Branch | Resolution | Date | Note |
|---|--------|------------|------|------|
| 1 | `origin/copilot-pull-request-reviewer/audit-github-history` | ✅ PR CLOSED | 2026-05-09 | PR #85 closed (empty bot PR, 0 files changed) |

### Section C.4: No PR Found — Resolved

| # | Branch | Resolution | Date | Note |
|---|--------|------------|------|------|
| 1 | `origin/codex/wo-frictionless-closeout` | 🔒 PRESERVED | 2026-05-09 | 16 unique commits, no PR, kept on remote |
| 2 | `origin/feat/e-v1-daemon-run` | ✅ DELETED | 2026-05-09 | Phase 5 cleanup |

### Section C.5: Dependabot Branches — ALL AUTO-CLOSED

| # | Branch | Resolution | Date | Note |
|---|--------|------------|------|------|
| 1 | `origin/dependabot/pip/filelock-gte-3.25.2` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 2 | `origin/dependabot/pip/mypy-gte-1.20.1` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 3 | `origin/dependabot/pip/pypy-gte-3.0.2` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 4 | `origin/dependabot/pip/plotly-gte-6.7.0` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted (plotly was ghost dep) |
| 5 | `origin/dependabot/pip/pytest-env-gte-1.6.0` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 6 | `origin/dependabot/pip/ruamel-yaml-gte-0.19.1` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 7 | `origin/dependabot/pip/safety-gte-3.7.0` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 8 | `origin/dependabot/pip/tree-sitter-gte-0.25.2` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted (floor manually updated) |
| 9 | `origin/dependabot/pip/typer-gte-0.24.1` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |
| 10 | `origin/dependabot/pip/types-pyyaml-gte-6.0.12.20260408` | ✅ AUTO-CLOSED | 2026-05-06 | dependabot.yml deleted |

### Summary: 31 → 7 Remote Branches

| Category | Original | Deleted | Preserved |
|----------|----------|---------|-----------|
| Fully merged (Section A) | 4 | 4 | 0 |
| Squash-merged (Section B) | 3 | 3 | 0 |
| Merged PRs squash (C.1) | 4 | 4 | 0 |
| Closed PRs (C.2) | 6 | 4 | 2 (+1 PRESERVED) |
| Open PRs (C.3) | 1 | 1 | 0 |
| No PR / orphan (C.4) | 2 | 1 | 1 |
| Dependabot (C.5) | 10 | 10 | 0 |
| **Total** | **30** (+ main) | **27** | **4** (+ main + 2 hygiene) |
