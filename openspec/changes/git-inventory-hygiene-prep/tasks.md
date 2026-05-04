# Tasks: Git Hygiene Report

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250-300 (single markdown file, dependabot/Tier 3 use compact table format) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Complete git-hygiene-report.md | PR 1 | Single documentation artifact |

## Phase 1: Skeleton + Executive Summary

- [ ] 1.1 Create `openspec/changes/git-inventory-hygiene-prep/git-hygiene-report.md` — header, purpose statement, 6 section headers (Executive Summary with entity-to-tier mapping, Tier 1, Tier 2, Tier 3, Accepted, Verification Checklist)
- [ ] 1.2 Write Executive Summary: entity-to-tier mapping table (14 rows per spec), 3-tier action counts
- [ ] 1.3 Write `.mailmap` spec section with exact file content mapping 3 identities → canonical `Felipe Gonzalez <felipe.gonzalez@users.noreply.github.com>`, source: exploration §Git Config → Author Identity

## Phase 2: Tier 1 — Immediate Actions

- [ ] 2.1 Write A-1-1 through A-1-4: branch delete actions for 4 fully-merged branches (feat/documentation-skill-phase1, fegome90-cmd/wo-skills-system, job/WO-0042, job/WO-0052), each with Prerequisite (SHA recording), command, rollback using recorded SHA, verify, source: exploration §Branches → Merged
- [ ] 2.2 Write A-1-5 through A-1-13: ghost config cleanup actions for 9 stale tracking entries (feat/wo-WO-0011, codex/chore-wo-hygiene, codex/ci-main-unblock, codex/wo-hygiene-rebase, codex/wo-guard-wave1, codex/wo-take-immediate-validation, codex/chore-wo-hygiene-safe, codex/merge-trifecta-wo-sidecar-hardening, codex/main-consolidation), source: exploration §Stale Local Branch Config Entries

## Phase 3: Tier 2 — Investigation Required

- [ ] 3.1 Write A-2-1 through A-2-10: dependabot PR triage actions (PRs #93–102) with merge/close recommendation per dependency, source: exploration §Open PRs
- [ ] 3.2 Write A-2-11 through A-2-17: orphan branch investigation for 7 unmerged no-PR branches (codex/wo-frictionless-closeout, feat/e-v1-daemon-run, feat/wo-WO-0042, feat/wo-WO-0044, feat/wo-WO-0047, fegome90-cmd/wo-0015-work, fix/wo-0055-code-review-issues), source: exploration §Branches
- [ ] 3.3 Write A-2-18 through A-2-22: closed-PR branch actions for 5 branches with unmerged commits (fix/search-context-preview-truncation, codex/batch-2d-runtime-manager, codex/docs-skillhub-context-refresh-20260327, codex/wo-remediation-ci-baseline, feat/skills-contracts-explain), risk=HIGH (code NOT in main, PR closed without merge — per spec §Risk Assessment), requires developer confirmation before deletion, source: exploration §Branches NOT merged
- [ ] 3.4 Write A-2-23 through A-2-25: squash-merged branch actions for 3 branches (codex/skill-hub-ssot-rebuild PR #103, codex/skill-hub-authority-anchor-closeout PR #86, codex/graph-mvp PR #74), risk=MEDIUM (code in main via squash merge but commit history not preserved — per spec §Risk Assessment), prerequisite SHA recording, source: exploration §Branches NOT merged
- [ ] 3.5 Write stash disposition action: risk=HIGH, options=preserve-on-branch | document-as-frozen, NO drop option, source: exploration §Stashes
- [ ] 3.6 Write hook path verification action: confirm whether `scripts/hooks/` or `.git/hooks/` is active, source: exploration §Hooks

## Phase 4: Tier 3 — Improvements

- [ ] 4.1 Write issue labeling action: 6 issues (#87–92) lack classification labels, source: exploration §Open Issues
- [ ] 4.2 Write PR #85 closure recommendation: close copilot WIP draft (stale 4 weeks), after closure delete remote branch copilot-pull-request-reviewer/audit-github-history (LOW risk), source: exploration §Open PRs
- [ ] 4.3 Write CODEOWNERS consideration note for future scaling, source: exploration §Risks
- [ ] 4.4 Write CI/CD `continue-on-error` review note (INFO risk, Accepted disposition, cross-reference to Accepted section), source: exploration §CI/CD
- [ ] 4.5 Write versioning tag strategy note (INFO risk, Accepted disposition, cross-reference to Accepted section), source: exploration §Tags

## Phase 5: Accepted Entities + Verification

- [ ] 5.1 Write Accepted section: Tags (3 safety tags, archival purpose) and CI/CD (well-configured) with "Accepted — no action needed" disposition
- [ ] 5.2 Write verification checklist section with commands: `git branch -r | wc -l`, `git shortlog -se`, `git stash list`, `git config --list` ghost-check
- [ ] 5.3 Self-review against proposal success criteria: entity-to-tier mapping complete (14 rows), all T1 actions have SHA recording + rollback, mailmap spec correct, stash preserve-only, all 9 risks covered, all 30 non-main branches dispositioned, report under 300 lines
