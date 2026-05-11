# Git Hygiene — Document Authority Registry

> **Date**: 2026-05-09
> **Purpose**: Declare authoritative vs historical/superseded status for every document in the Git Hygiene cycle.

---

## Current Authority

These documents contain **actionable** or **resolved** state. Their resolution sections are the source of truth.

### summary-20260504.md
- **Authority scope**: Only the **Post-Audit Resolution (Updated 2026-05-09)** section at the bottom.
- The original audit tables, stash section, ghost section, and "Next Safe Commands" are **historical**.
- Do NOT execute commands from "Next Safe Commands" — all are resolved per the "Updated Next Safe Commands Status" table.

### branch-audit-20260504.md
- **Authority scope**: Only the **Resolution Status (Updated 2026-05-09)** section at the bottom.
- Original Section C.5 contains a known typo: `pypy-gte-3.0.2` should be `pandas-gte-3.0.2` (PR #102 is pandas, not pypy).
- Original classification tables may contain stale branch names; always cross-reference with Resolution Status.

### phase-3-closeout-20260504.md
- **Authority scope**: Full document — authoritative for stash/patch closeout state.
- Documents the Phase 3 working tree stabilization and stash preservation.

### closed-pr-semantic-memo-20260509.md
- **Authority scope**: Full document — authoritative for closed-PR branch PRESERVED vs DELETED classification rationale.
- Documents the decision criteria, evidence sources, and uncertainties for each branch decision.
- This is the semantic trace for destructive decisions already taken — do NOT reclassify without updating this memo.

### closed-pr-semantic-memo-correction-20260509.md
- **Authority scope**: Full document — correction to the closed-pr semantic memo.
- Adds evidence strength column per deleted branch, adjusts Rule 5 for honest post-hoc classification, and documents accepted residual risks.
- This correction does NOT revert any operational decision.

### post-audit-execution-20260504.md
- **Authority scope**: Full document — authoritative for Phase 2 execution evidence.
- Records the actual commands executed and their outcomes during Phase 2.

### stash-retention-policy-20260509.md
- **Authority scope**: Full document — authoritative for stash preservation branch retention policy.
- Audits content of `origin/hygiene/stash-preserve-codex-freeze` (310 files, commit `07a8cf4d`), evaluates 4 retention options, and implements Option B (annotated tag + maintain branch).
- Status: ACCEPTED / IMPLEMENTED — tag `stash-preserve-codex-freeze-v1` created, branch maintained.

### stash-retention-policy-implementation-20260509.md
- **Authority scope**: Full document — implementation report for stash retention policy execution.
- Records tag creation, SHA verification, actions not taken, and residual risks.
- Includes commit provenance section (policy drafts `6d47e3c4`/`e314914b`, implementation `c6c55cb9`).

### stash-retention-policy-correction-20260509.md
- **Authority scope**: Full document — correction report for stash retention policy documentation.
- Corrects "zero data loss risk" → "low data-loss risk, not zero" and "sole remaining preservation" → "primary material preservation".
- Clarifies commit provenance (README had incorrect `03eede58`; corrected to `c6c55cb9`).
- No operational changes — tag, branch, and decision (Option B) unchanged.

### dependabot-policy-20260509.md
- **Authority scope**: Full document — DRAFT dependabot policy awaiting human review.
- Audits current dependency inventory, reconstructs PR #93-#102 history, classifies dependencies by risk (LOW/MEDIUM/HIGH/SECURITY), proposes improved dependabot.yml config with lower queue limits and major-update ignore rules.
- **Status**: DRAFT — no operational changes until human approval.

---

## Historical / Superseded

These documents are retained for audit trail only. Do NOT execute any commands from them.

| Document | Status | Reason |
|----------|--------|--------|
| `dependabot-phase-4-plan-20260504.md` | **SUPERSEDED** | All 10 dependabot PRs were auto-closed after `dependabot.yml` was deleted. Merge plan is void. Remaining action: recreate `dependabot.yml` and handle mypy floor update in a future SDD cycle. |
| `preflight-20260504.md` | **HISTORICAL** | Preflight data collected before audit. `.mailmap` was created in Phase 2. |
| `stash-audit-20260504.md` | **HISTORICAL** | Stash was dropped in Phase 4. Content preserved on remote branch `origin/hygiene/stash-preserve-codex-freeze`. |
| `ghost-cleanup-plan-20260504.md` | **HISTORICAL** | Ghost config cleanup executed in Phase 2. Plan is void. |
| `ghost-entries-backup-20260504.txt` | **HISTORICAL** | Backup of ghost config before cleanup. Retained for audit trail. |
| `ghost-before-20260504.txt` | **HISTORICAL** | Snapshot before ghost cleanup. Retained for audit trail. |
| `ghost-after-20260504.txt` | **HISTORICAL** | Snapshot after ghost cleanup. Retained for audit trail. |

---

## Known Corrections

| Correction | Source | Detail |
|-----------|--------|--------|
| PR #102 is pandas, not pypy | `branch-audit-20260504.md` Section C.5 | The branch name `dependabot/pip/pypy-gte-3.0.2` is incorrect. The package is **pandas** (`dependabot/pip/pandas-gte-3.0.2`). The `dependabot-phase-4-plan` correctly identifies it as pandas. |
| Dependabot PRs were NOT merged | `dependabot-phase-4-plan-20260504.md` | All 10 Dependabot PRs (#93-#102) were **auto-closed** after `dependabot.yml` was deleted from the repo. None were merged. |
| Stash was dropped in Phase 4 | `stash-audit-20260504.md`, `summary-20260504.md` | `stash@{0}` was dropped during Phase 4 closeout. Content remains preserved on remote branch `origin/hygiene/stash-preserve-codex-freeze`. |
| Archive branches deleted in Phase 4 | `branch-audit-20260504.md` | All 7 `archive/*` remote branches were deleted in Phase 4 after prior preservation. |
| Closed-PR branch count | `phase-2-closeout-20260504.md` | Original text stated "6 closed-PR branches resolved: 5 deleted..." which was inaccurate. 3 were PRESERVED and 3 were DELETED. |
| Stash retention risk phrasing | `stash-retention-policy-20260509.md` | "Zero data loss risk" was inaccurate — both tag and branch depend on the same remote. Corrected to "Low data-loss risk, not zero". See `stash-retention-policy-correction-20260509.md`. |
| Stash retention "sole preservation" | `stash-retention-policy-20260509.md` | "Sole remaining preservation" became obsolete after tag creation. Corrected to acknowledge tag as additional reference. See `stash-retention-policy-correction-20260509.md`. |
| Implementation commit hash in README | `hygiene/README.md` | Listed `03eede58` as implementation commit. Actual commit is `c6c55cb9`. Corrected. See `stash-retention-policy-correction-20260509.md`. |

---

## Authority Map by Topic

| Topic | Authoritative Document | Section |
|-------|----------------------|---------|
| Branch fate (deleted vs preserved) | `branch-audit-20260504.md` | Resolution Status (Updated 2026-05-09) |
| Branch decision rationale (PRESERVED vs DELETED) | `closed-pr-semantic-memo-20260509.md` | Full document |
| Branch decision evidence strength + residual risk | `closed-pr-semantic-memo-correction-20260509.md` | Full document |
| Current remote branches (7 remaining) | `summary-20260504.md` | Post-Audit Resolution → Current Remote Branches |
| Stash state (dropped, content on branch) | `summary-20260504.md` | Post-Audit Resolution → Updated "Next Safe Commands" Status |
| Dependabot resolution | `dependabot-phase-4-plan-20260504.md` | Resolution (Updated 2026-05-09) |
| Phase execution evidence | `post-audit-execution-20260504.md` | Full document |
| Stash/patch closeout | `phase-3-closeout-20260504.md` | Full document |
| Stash retention policy | `stash-retention-policy-20260509.md` | Full document (IMPLEMENTED) |
| Stash retention implementation | `stash-retention-policy-implementation-20260509.md` | Full document |
| Stash retention corrections | `stash-retention-policy-correction-20260509.md` | Full document |
| Dependabot policy (draft) | `dependabot-policy-20260509.md` | Full document (DRAFT) |
| Dependabot PR history | `dependabot-policy-20260509.md` | Section 3 |
| Phase 2 execution log | `phase-2-closeout-20260504.md` | Full document |
| Ghost cleanup evidence | `ghost-before/after-20260504.txt` | Snapshots (historical) |

---

## Residual Risks

1. **`dependabot.yml` must be recreated** — Without it, Dependabot will not open new PRs for security updates.
2. **mypy floor update pending** — mypy >=1.20.1 was auto-closed; the floor update needs a separate SDD cycle.
3. **`codex/wo-frictionless-closeout`** — Preserved with 16 unique commits and no PR. Requires human decision on integration or archival.
4. **Large patch artifacts** — `_ctx/handoff/WO-0005/diff.patch` (57.9 MB) and `tests/fixtures/.../reconcile.patch` (83.26 MB) still present.
5. **`hygiene/stash-20260504.patch`** — 100.64 MB. **Deleted in Phase 3** (redundant; exceeded GitHub 100 MB push limit). Content preserved in remote branch `origin/hygiene/stash-preserve-codex-freeze` (commit `07a8cf4d`). See `phase-3-closeout-20260504.md`.
