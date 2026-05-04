# Design: Git Hygiene Report

## Technical Approach

The report is a **hand-curated Markdown document** that transforms exploration data into an actionable execution plan. No code is generated; a human reads the exploration findings, applies judgment on risk/disposition, and writes the report. The design specifies the report's structure, data sources per section, and verification criteria.

## Architecture Decisions

| # | Decision | Choice | Alternatives | Rationale |
|---|----------|--------|--------------|-----------|
| 1 | Report format | Markdown | JSON, YAML | Human-readable, diff-friendly, matches openspec convention. No parsing needed — the consumer is the developer, not a tool. |
| 2 | Report location | `openspec/changes/git-inventory-hygiene-prep/git-hygiene-report.md` | `docs/`, repo root | openspec is the artifact store for this change. Report is a change artifact, not permanent documentation. |
| 3 | Generation method | Hand-curated from exploration | Script-generated | Exploration data requires judgment (is this branch safe to delete?). Automation would need complex heuristics for a one-time task. |
| 4 | Traceability | Exploration section → recommendation | Inline notes | Each recommendation cites the exploration finding it derives from (e.g., "Branches §Remote — NOT merged row 3"). |
| 5 | Connection to hygiene phase | Report IS the execution plan | Separate issue/PR | Each Tier 1 action includes exact commands — the hygiene phase runs those commands. No intermediate step needed. |

## Data Flow

```
exploration.md ──→ Human judgment ──→ git-hygiene-report.md
      │                                        │
      │ §Branches          ──→ §Branch Cleanup │
      │ §Stashes           ──→ §Stash Plan     │
      │ §Git Config        ──→ §Config Cleanup │
      │ §Hooks             ──→ §Hook Fix       │
      │ §Open PRs/Issues   ──→ §PR/Issue Plan  │
      │ §Author Identity   ──→ §Mailmap Spec   │
      │ §CI/CD             ──→ §Accepted       │
      │ §Tags              ──→ §Accepted       │
      │                                         │
      └─── Verification ◄─── git commands ──────┘
```

## Report Structure

The report organizes content by priority tier. Each action explicitly tags which exploration entity it addresses (per the entity-to-tier mapping in the spec).

| Section | Source | Content |
|---------|--------|---------|
| Executive Summary | Proposal §Approach | 3-tier overview with entity-to-tier mapping table (14 entity rows) |
| Tier 1 — Immediate Actions | Exploration §Branches (merged: 4), §Git Config, §Author Identity | `.mailmap` spec, 4 safe branch deletes (fully merged only), 9 ghost entry cleanups — each with command, rollback, verify |
| Tier 2 — Investigation Required | Exploration §Branches (NOT merged), §Stashes, §Hooks, §Open PRs | 10 dependabot triage, 7 orphan branches, 5 closed-PR branches (unmerged commits, HIGH risk), 3 squash-merged branches (MEDIUM risk), stash disposition (resolved: preserve-only, HIGH risk, no drop), hook path verification |
| Tier 3 — Improvements | Exploration §Open PRs/Issues, §Risks | Issue labeling, PR #85 closure, CODEOWNERS consideration, CI/CD `continue-on-error` review note, versioning tag strategy note |
| Accepted — No Action | Exploration §Tags, §CI/CD | Tags (3 safety tags serve archival purpose), CI/CD (well-configured) |
| Verification Checklist | All sections | Commands to confirm each action completed correctly |

Each action within a tier uses this template:

```markdown
### A-{tier}-{seq}: {Title}
- **Entity**: {Branches|Stashes|Config|Hooks|PRs|Issues|Author Identity}
- **Risk**: {Info|Low|Medium|High}
- **Prerequisite**: `{command to record state, e.g. git rev-parse origin/<branch>}`
- **Command**: `{exact git command}`
- **Expected**: {what happens on success}
- **Rollback**: `{command to undo, using recorded state from Prerequisite}`
- **Verify**: `{command to confirm}`
- **Source**: exploration §{section}
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/git-inventory-hygiene-prep/git-hygiene-report.md` | Create | Main report artifact — structured, actionable hygiene execution plan |

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Verification | Report completeness | Checklist: all 30 non-main remote branches dispositioned, all 3 tiers populated, every Tier 1 action has command+rollback |
| Verification | `.mailmap` accuracy | `git shortlog -se` after creation — should show unified identity |
| Verification | Branch count | `git branch -r | wc -l` before/after hygiene execution |

## Migration / Rollout

No migration required. This is a documentation artifact. The report itself serves as the rollback plan: every Tier 1 action includes an undo command.

## Open Questions

None. Stash@{0} disposition is resolved: risk=HIGH, "drop" is NOT an option. Options are "apply to named branch" or "document as intentionally frozen". No report-writing tasks are blocked. During hygiene execution, Task 3.5 (stash disposition choice) and Task 3.3 (closed-PR branch confirmation) require developer input. All other tasks proceed independently.
