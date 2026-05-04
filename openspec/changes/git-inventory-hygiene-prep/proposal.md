# Proposal: Git Inventory Hygiene Prep

## Intent

Produce a structured, priority-ranked git hygiene report from the exploration data so the developer can execute cleanup safely — with rollback strategies and risk assessment per action. No code changes; purely a documentation artifact.

## Scope

### In Scope
- Structured hygiene report with 3 priority tiers (immediate / investigate / improvement)
- Per-action risk level, rollback strategy, and verification command
- Branch cleanup plan: 4 safe-deletes (fully merged), 3 cautious deletes (squash-merged, MEDIUM risk), 5 closed-PR branches (investigation, HIGH risk), 7 orphan branches (investigation), 10 dependabot triages
- `.mailmap` specification for author identity unification (3 → 1)
- Stash disposition (HIGH risk, preserve-only, no drop)
- Hook path conflict resolution guidance
- Ghost config entry cleanup checklist
- Issue labeling recommendations
- CI/CD `continue-on-error` review note
- Versioning tag strategy note

### Out of Scope
- **Executing** any cleanup (branch deletion, stash drop, etc.)
- Code changes to any source file
- CI/CD pipeline modifications
- `.mailmap` file creation (report specifies what it should contain; creation is the hygiene phase)
- Dependabot PR reviews (report flags them; merging is the hygiene phase)

## Capabilities

### New Capabilities
- `git-hygiene-report`: Structured audit report artifact with priority-ranked actions, risk assessment, rollback strategies, and verification commands — serves as the execution plan for the hygiene phase.

### Modified Capabilities
None — this change introduces a standalone documentation artifact.

## Approach

The exploration already captured the full inventory. The report packages findings into an actionable execution plan:

1. **Tier 1 — Immediate** (low risk): `.mailmap` spec, 4 safe branch deletes (fully merged only), 9 ghost config cleanups
2. **Tier 2 — Investigate** (medium-high risk): 10 dependabot PR triage, 7 orphan branches, 5 closed-PR branches (unmerged commits, HIGH risk), 3 squash-merged branches (MEDIUM risk), stash disposition, hook path verification
3. **Tier 3 — Improvements** (low risk): issue labeling, PR #85 + copilot branch closure, CODEOWNERS consideration, CI/CD note, versioning tags note

Each action includes: exact commands, expected outcome, rollback command, and verification step.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/git-inventory-hygiene-prep/` | New | Report artifact location |
| `.mailmap` | Deferred | Specified in report, created in hygiene phase |
| `.git/config` | Deferred | Ghost entries documented for cleanup |
| Remote branches (4) | Deferred | Fully-merged safe-delete candidates documented |
| Remote branches (3) | Deferred | Squash-merged cautious-delete candidates (MEDIUM risk) |
| Remote branches (12) | Deferred | Closed-PR and orphan branches for investigation |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Stash loss during hygiene execution | Medium | Report marks stash as "preserve first, no drop" — stash actions only offer apply-to-branch or document-as-frozen |
| Wrong branch deleted | Low | Every branch action records tip SHA before deletion and restores via `git push origin {sha}:refs/heads/{branch}` |
| `.mailmap` errors | Low | Report includes exact file content; validation via `git shortlog -se` |

## Rollback Plan

This is a documentation-only change — no rollback needed. The report itself IS the rollback plan for the hygiene phase: every action includes an undo command.

## Dependencies

- Exploration artifact: `openspec/changes/git-inventory-hygiene-prep/exploration.md` (complete)

## Success Criteria

- [ ] Report uses tier-based structure with entity-to-tier mapping covering all 14 entity rows
- [ ] Every Tier 1 action includes exact git commands, SHA recording prerequisite, and rollback
- [ ] `.mailmap` specification is correct (verifiable via `git shortlog`)
- [ ] Stash disposition is explicitly "preserve-only" with no drop option
- [ ] All 9 exploration risks are covered with action or "Accepted" disposition
- [ ] Report is under 300 lines (actionable, not encyclopedic)
