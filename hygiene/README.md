# Git Hygiene Documentation — Index

> **Authority registry**: See `git-hygiene-document-authority-20260509.md` for which documents are current authority vs historical/superseded.
> **Do NOT execute commands** from documents marked as HISTORICAL or SUPERSEDED.

---

## Current Authority (actionable / resolved)

| File | Purpose | Status |
|------|---------|--------|
| `git-hygiene-document-authority-20260509.md` | Central registry: which docs are authority, which are historical, known corrections | **AUTHORITY** |
| `closed-pr-semantic-memo-20260509.md` | Rationale for PRESERVED vs DELETED closed-PR branch decisions | **AUTHORITY** |
| `phase-6-document-authority-fix-20260509.md` | Report of document authority corrections applied (STATUS headers, contradictions fixed) | **AUTHORITY** |
| `summary-20260504.md` | Overall audit summary — only **Post-Audit Resolution** section is authoritative | HISTORICAL body + AUTHORITATIVE appendix |
| `branch-audit-20260504.md` | Full branch classification — only **Resolution Status** section is authoritative | HISTORICAL body + AUTHORITATIVE appendix |
| `post-audit-execution-20260504.md` | Phase 2+4+5 execution evidence with actual commands run | **AUTHORITY** |
| `phase-3-closeout-20260504.md` | Stash/patch closeout state | **AUTHORITY** |
| `phase-2-closeout-20260504.md` | Phase 2 closeout with residual risks resolved | HISTORICAL body + AUTHORITATIVE appendix |

## Historical / Superseded (audit trail only)

| File | Purpose | Status |
|------|---------|--------|
| `dependabot-phase-4-plan-20260504.md` | Merge plan for 10 dependabot PRs — all auto-closed | **SUPERSEDED** |
| `preflight-20260504.md` | Pre-audit data collection + .mailmap proposal | HISTORICAL |
| `stash-audit-20260504.md` | Initial stash audit — stash dropped in Phase 4 | HISTORICAL |
| `sha-registry-20260504.md` | All audited branch tip SHAs (historical snapshot) | HISTORICAL |
| `phase-3-working-tree-stabilization-20260504.md` | Working tree stabilization audit | HISTORICAL |
| `ghost-cleanup-plan-20260504.md` | Ghost config cleanup plan — executed in Phase 2 | HISTORICAL |
| `ghost-entries-backup-20260504.txt` | Raw ghost config backup | EVIDENCE |
| `ghost-before-20260504.txt` | Config snapshot before cleanup | EVIDENCE |
| `ghost-after-20260504.txt` | Config snapshot after cleanup | EVIDENCE |

---

## Chronological Timeline

| Date | Phase | Key Commit | What |
|------|-------|-----------|------|
| 2026-05-04 | Audit | `3bc2473e` | Initial audit: 31 remote branches, 9 ghost entries, stash preserved |
| 2026-05-04 | Phase 2 | `172a943c`–`985106fe` | Ghost cleanup, .mailmap, 11 branches archived/deleted |
| 2026-05-04 | Phase 3 | `86cfa5d4` | Patch deleted, .gitignore updated, working tree stabilized |
| 2026-05-06 | Phase 4 | `49031bd2` | Closeout: 3 stashes dropped, 5 worktrees removed, 7 archive branches deleted |
| 2026-05-09 | Phase 5 | `e6e115d0` | Cleanup: dead hook, PR #85, labels, plotly removed, tree-sitter floors, 12 remote branches deleted |
| 2026-05-09 | Docs anchor | `e2627999` | Hygiene docs cherry-picked to main from remote branch |
| 2026-05-09 | Docs update | `5a201707` | Phase 4+5 resolution appended to all anchor docs |
| 2026-05-09 | Phase 6 | `f50bc595` | Document authority fix: STATUS headers, authority registry, contradiction corrections |
| 2026-05-09 | Archive | engram #2747 | SDD change archived. Follow-ups registered. |
| 2026-05-09 | Follow-up 1 | `c6ea4112` | Closed-PR semantic memo: PRESERVED vs DELETED rationale |

---

## Open Follow-ups

| Priority | Change | Engram | Status |
|----------|--------|--------|--------|
| 1 | Closed-PR semantic memo | #2750, #2751 | ✅ Complete |
| 2 | Stash retention policy | #2749 | Pending |
| 3 | Dependabot policy | #2748 | Pending |
