# Phase 6: Document Authority Fix — Report

> **Date**: 2026-05-09
> **Scope**: Documentation-only. No operational Git changes.
> **Commit**: `docs: clarify git hygiene document authority`

---

## Files Modified

| File | Action | What Was Done |
|------|--------|---------------|
| `hygiene/git-hygiene-document-authority-20260509.md` | CREATED | Authority registry declaring current vs superseded documents |
| `hygiene/summary-20260504.md` | MODIFIED | Inserted STATUS warning at top; original "Next Safe Commands" marked as historical |
| `hygiene/dependabot-phase-4-plan-20260504.md` | MODIFIED | Inserted SUPERSEDED warning at top |
| `hygiene/branch-audit-20260504.md` | MODIFIED | Inserted HISTORICAL AUDIT + RESOLUTION warning at top; noted pypy/pandas typo |
| `hygiene/phase-2-closeout-20260504.md` | MODIFIED | Replaced ambiguous "5 deleted" phrase with exact PRESERVED/DELETED classification |
| `hygiene/phase-6-document-authority-fix-20260509.md` | CREATED | This report |

---

## Contradictions Corrected

| Contradiction | Location | Correction |
|--------------|----------|------------|
| "6 closed-PR branches resolved: 5 deleted..." was inaccurate and misleading | `phase-2-closeout-20260504.md` | Replaced with exact list: 3 PRESERVED, 3 DELETED |
| Summary's "Next Safe Commands" appeared as actionable runbook | `summary-20260504.md` | Inserted visible STATUS block warning not to execute these commands |
| Dependabot merge plan appeared as active plan | `dependabot-phase-4-plan-20260504.md` | Inserted SUPERSEDED block at top |
| Branch audit tables contained stale data without warning | `branch-audit-20260504.md` | Inserted HISTORICAL AUDIT + RESOLUTION block noting stale names and typo |

---

## Documents Marked as Superseded

| Document | Status |
|----------|--------|
| `dependabot-phase-4-plan-20260504.md` | SUPERSEDED — merge plan void; all PRs auto-closed |

---

## Documents Marked as Historical

| Document | Status |
|----------|--------|
| `summary-20260504.md` | HISTORICAL SUMMARY — only Post-Audit Resolution section is authoritative |
| `branch-audit-20260504.md` | HISTORICAL AUDIT — only Resolution Status section is authoritative |
| `preflight-20260504.md` | HISTORICAL — pre-audit data collection |
| `stash-audit-20260504.md` | HISTORICAL — stash dropped in Phase 4 |
| `ghost-cleanup-plan-20260504.md` | HISTORICAL — executed in Phase 2 |
| `ghost-entries-backup-20260504.txt` | HISTORICAL — pre-cleanup backup |
| `ghost-before-20260504.txt` | HISTORICAL — before snapshot |
| `ghost-after-20260504.txt` | HISTORICAL — after snapshot |

---

## Current Authority by Topic

| Topic | Authoritative Document | Section |
|-------|----------------------|---------|
| Branch fate (31→7) | `branch-audit-20260504.md` | Resolution Status (Updated 2026-05-09) |
| Current remote branches | `summary-20260504.md` | Post-Audit Resolution → Current Remote Branches |
| Dependabot resolution | `dependabot-phase-4-plan-20260504.md` | Resolution (Updated 2026-05-09) |
| Stash state | `summary-20260504.md` | Updated "Next Safe Commands" Status |
| Phase execution evidence | `post-audit-execution-20260504.md` | Full document |
| Document authority registry | `git-hygiene-document-authority-20260509.md` | Full document |

---

## Residual Risks

1. **`dependabot.yml` not recreated** — No automated dependency updates until recreated.
2. **mypy floor update pending** — Needs separate SDD cycle.
3. **`codex/wo-frictionless-closeout`** — 16 unique commits preserved, no PR. Awaiting human decision.
4. **Large patch artifacts** — `diff.patch` (57.9 MB), `reconcile.patch` (83.26 MB) still present. **`stash-20260504.patch` was deleted in Phase 3** (redundant; exceeded GitHub 100 MB push limit). Content preserved on remote branch `origin/hygiene/stash-preserve-codex-freeze` (commit `07a8cf4d`). See `phase-3-closeout-20260504.md` for details.
5. **Future agents** — Must consult `git-hygiene-document-authority-20260509.md` before acting on any hygiene document.
