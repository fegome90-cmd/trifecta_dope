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

### dependabot-policy-correction-20260509.md
- **Authority scope**: Full document — correction report for dependabot policy documentation.
- Corrects authority registry claims: dependabot.yml was NOT deleted, PRs had mixed outcomes (5 merged, 5 closed). Upgrades mypy from LOW to MEDIUM risk. Adds major update policy section. Adds semver-major ignores for filelock, jsonschema, tiktoken, pyyaml.
- No operational changes — `.github/dependabot.yml` not modified.

### dependabot-policy-semver-correction-20260509.md
- **Authority scope**: Full document — semver 0.x risk correction report for dependabot policy.
- Documents the 0.x SemVer risk: packages at `0.x` (typer*, tree-sitter*, ruamel.yaml, tiktoken) can have breaking semver-minor bumps. Adds semver-minor ignores for affected packages. Corrects Major Update Policy for explicit tier handling. Adds `prod-cli` group. Syncs grouping table with YAML conceptual config.
- No operational changes — `.github/dependabot.yml` not modified.

### dependabot-policy-high-patch-only-correction-20260509.md
- **Authority scope**: Full document — HIGH patch-only consistency correction report for dependabot policy.
- Corrects contradiction: policy said "HIGH = patch-only" but YAML conceptual only ignored semver-major for stable HIGH packages. Added semver-minor ignores for pandas, pydantic, filelock, jsonschema, pyyaml/PyYAML. Corrected Section 5.4 major update rule. Updated YAML comments. All HIGH packages now patch-only by Dependabot.
- No operational changes — `.github/dependabot.yml` not modified.

---

## Historical / Superseded

These documents are retained for audit trail only. Do NOT execute any commands from them.

| Document | Status | Reason |
|----------|--------|--------|
| `dependabot-phase-4-plan-20260504.md` | **SUPERSEDED** | `dependabot.yml` was NOT deleted — Dependabot remained active. PRs #93-#102 had mixed outcomes: 5 MERGED (#94 safety, #97 filelock, #99 ruamel-yaml, #101 pytest-env, #102 pandas), 5 CLOSED (#93 typer, #95 types-pyyaml, #96 mypy, #98 tree-sitter, #100 plotly). Merge plan is void. Current authority: `dependabot-policy-20260509.md`. |
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
| Dependabot PRs had mixed outcomes (not all auto-closed) | `dependabot-phase-4-plan-20260504.md` | Phase 4 docs stated all 10 PRs were auto-closed after `dependabot.yml` was deleted. In fact, `dependabot.yml` was NOT deleted and 5 of 10 PRs were **MERGED** (#94, #97, #99, #101, #102). Only 5 were CLOSED (#93, #95, #96, #98, #100). Corrected in `dependabot-policy-20260509.md` Section 3 and `dependabot-policy-correction-20260509.md`. |
| Stash was dropped in Phase 4 | `stash-audit-20260504.md`, `summary-20260504.md` | `stash@{0}` was dropped during Phase 4 closeout. Content remains preserved on remote branch `origin/hygiene/stash-preserve-codex-freeze`. |
| Archive branches deleted in Phase 4 | `branch-audit-20260504.md` | All 7 `archive/*` remote branches were deleted in Phase 4 after prior preservation. |
| Closed-PR branch count | `phase-2-closeout-20260504.md` | Original text stated "6 closed-PR branches resolved: 5 deleted..." which was inaccurate. 3 were PRESERVED and 3 were DELETED. |
| Stash retention risk phrasing | `stash-retention-policy-20260509.md` | "Zero data loss risk" was inaccurate — both tag and branch depend on the same remote. Corrected to "Low data-loss risk, not zero". See `stash-retention-policy-correction-20260509.md`. |
| Stash retention "sole preservation" | `stash-retention-policy-20260509.md` | "Sole remaining preservation" became obsolete after tag creation. Corrected to acknowledge tag as additional reference. See `stash-retention-policy-correction-20260509.md`. |
| Implementation commit hash in README | `hygiene/README.md` | Listed `03eede58` as implementation commit. Actual commit is `c6c55cb9`. Corrected. See `stash-retention-policy-correction-20260509.md`. |
| mypy risk classification | `dependabot-policy-20260509.md` | Originally classified as LOW. Upgraded to MEDIUM — touches the type gate and can break CI. See `dependabot-policy-correction-20260509.md`. |
| Dependabot authority source | `git-hygiene-document-authority-20260509.md` | Authority Map previously pointed to `dependabot-phase-4-plan-20260504.md`. Updated to `dependabot-policy-20260509.md`. See `dependabot-policy-correction-20260509.md`. |
| 0.x SemVer risk not controlled | `dependabot-policy-20260509.md` | Original policy only blocked semver-major for HIGH packages, leaving 0.x packages (typer, tree-sitter, ruamel.yaml, tiktoken) vulnerable to breaking semver-minor bumps. Corrected: semver-minor ignores added for HIGH 0.x packages, Major Update Policy rewritten, prod-cli group added. See `dependabot-policy-semver-correction-20260509.md`. |
| HIGH patch-only inconsistency | `dependabot-policy-20260509.md` | Policy said "HIGH = patch-only" but YAML conceptual only ignored semver-major for stable HIGH packages (pandas, pydantic, filelock, jsonschema, pyyaml). Corrected: semver-minor ignores added for ALL HIGH packages. Section 5.4 rule rewritten. YAML comment fixed. See `dependabot-policy-high-patch-only-correction-20260509.md`. |

---

## Authority Map by Topic

| Topic | Authoritative Document | Section |
|-------|----------------------|---------|
| Branch fate (deleted vs preserved) | `branch-audit-20260504.md` | Resolution Status (Updated 2026-05-09) |
| Branch decision rationale (PRESERVED vs DELETED) | `closed-pr-semantic-memo-20260509.md` | Full document |
| Branch decision evidence strength + residual risk | `closed-pr-semantic-memo-correction-20260509.md` | Full document |
| Current remote branches (7 remaining) | `summary-20260504.md` | Post-Audit Resolution → Current Remote Branches |
| Stash state (dropped, content on branch) | `summary-20260504.md` | Post-Audit Resolution → Updated "Next Safe Commands" Status |
| Dependabot current policy / PR history | `dependabot-policy-20260509.md` | Full document (DRAFT) |
| Phase execution evidence | `post-audit-execution-20260504.md` | Full document |
| Stash/patch closeout | `phase-3-closeout-20260504.md` | Full document |
| Stash retention policy | `stash-retention-policy-20260509.md` | Full document (IMPLEMENTED) |
| Stash retention implementation | `stash-retention-policy-implementation-20260509.md` | Full document |
| Stash retention corrections | `stash-retention-policy-correction-20260509.md` | Full document |
| Dependabot policy (draft) | `dependabot-policy-20260509.md` | Full document (DRAFT) |
| Dependabot PR history | `dependabot-policy-20260509.md` | Section 3 |
| Dependabot policy corrections | `dependabot-policy-correction-20260509.md` | Full document |
| Dependabot semver 0.x corrections | `dependabot-policy-semver-correction-20260509.md` | Full document |
| Dependabot HIGH patch-only correction | `dependabot-policy-high-patch-only-correction-20260509.md` | Full document |
| Phase 2 execution log | `phase-2-closeout-20260504.md` | Full document |
| Ghost cleanup evidence | `ghost-before/after-20260504.txt` | Snapshots (historical) |

---

## Residual Risks

1. **`dependabot.yml` needs config update** — File exists and Dependabot IS active, but current config is overly permissive (limit: 10, no major-update ignores). Proposed config in `dependabot-policy-20260509.md` awaits human approval.
2. **mypy floor update pending** — mypy >=1.20.1 was auto-closed; the floor update needs a separate SDD cycle.
3. **`codex/wo-frictionless-closeout`** — Preserved with 16 unique commits and no PR. Requires human decision on integration or archival.
4. **Large patch artifacts** — `_ctx/handoff/WO-0005/diff.patch` (57.9 MB) and `tests/fixtures/.../reconcile.patch` (83.26 MB) still present.
5. **`hygiene/stash-20260504.patch`** — 100.64 MB. **Deleted in Phase 3** (redundant; exceeded GitHub 100 MB push limit). Content preserved in remote branch `origin/hygiene/stash-preserve-codex-freeze` (commit `07a8cf4d`). See `phase-3-closeout-20260504.md`.
