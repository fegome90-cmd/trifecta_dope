# Git Hygiene Report Specification

## Purpose

Structure and content requirements for a git hygiene audit report. The report prescribes actions but does NOT execute them.

## Requirements

### Requirement: Report Structure

The report SHALL organize content by priority tier (Executive Summary, Tier 1–3, Verification Checklist) with each action explicitly tagged to the exploration entity it addresses (Branches, Tags, Stashes, Hooks, Config, CI/CD, Open Items, Author Identity).

The following entity-to-tier mapping SHALL be documented in the Executive Summary:

| Entity | Tier | Disposition |
|--------|------|-------------|
| Author Identity | Tier 1 | `.mailmap` spec |
| Branches (fully merged) | Tier 1 | Safe delete (4 branches) |
| Config (ghost entries) | Tier 1 | Cleanup (9 entries) |
| Branches (dependabot) | Tier 2 | PR triage (10 PRs) |
| Branches (orphan) | Tier 2 | Investigation (7 branches) |
| Branches (closed-PR, unmerged) | Tier 2 | HIGH risk investigation (5 branches) |
| Branches (squash-merged) | Tier 2 | MEDIUM risk cautious delete (3 branches) |
| Stashes | Tier 2 | Disposition (1 stash) |
| Hooks | Tier 2 | Path verification |
| Open Items (Issues) | Tier 3 | Labeling (6 issues) |
| Open Items (PRs) | Tier 3 | Close stale (PR #85 + branch cleanup) |
| Tags | Accepted | No action — 3 safety tags serve archival purpose |
| CI/CD | Accepted | No action — well-configured, `continue-on-error` noted |
| CODEOWNERS | Tier 3 | Consideration note |

Each tier section MUST include: current state, risk assessment, actions (if any), and "Accepted — no action needed" when clean. Entities classified as "Accepted" MAY appear in a standalone Accepted section or within their respective tier section.

#### Scenario: Complete report covers all entity types

- GIVEN exploration data exists for all git entity types
- WHEN the report is generated
- THEN all 14 entity-row mappings are present in the Executive Summary table
- AND each entity has an action or "Accepted" disposition

#### Scenario: Accepted entity produces minimal entry

- GIVEN tags have no hygiene issues
- WHEN the Tags entry is written
- THEN it declares "Accepted — no action needed" with a one-line justification

### Requirement: Priority Classification

Every recommended action MUST be classified into exactly one priority tier.

| Tier | Label | Meaning | Execution Order |
|------|-------|---------|-----------------|
| P1 | Immediate | Low-risk, reversible, high signal | Execute first |
| P2 | Investigate | Requires human judgment or data review | Execute after P1 |
| P3 | Improvement | Optional enhancements, no urgency | Execute when convenient |

No action SHALL be classified into multiple tiers. P1 actions MUST NOT depend on P2 or P3 actions.

#### Scenario: P1 action is independently executable

- GIVEN a P1 action to delete a merged remote branch
- WHEN the action is executed
- THEN it succeeds without any P2 or P3 action being completed first
- AND a rollback command is provided

#### Scenario: P2 action flags investigation need

- GIVEN 10 dependabot PRs pending review
- WHEN the report classifies them as P2
- THEN each PR is listed with its current status and a triage recommendation

### Requirement: Risk Assessment

Each action MUST include a risk level (HIGH / MEDIUM / LOW / INFO) and a mitigation strategy.

- Stash disposition SHALL be HIGH risk with "preserve first" mitigation. "drop" is NOT an option.
- Branch deletion where PR was merged via squash/rebase SHALL be MEDIUM risk (original commit history is lost).
- Branch deletion where PR was closed without merge SHALL be HIGH risk (code changes are NOT in main).
- Branch deletion where `git merge-base --is-ancestor <branch> main` confirms full ancestry SHALL be LOW risk.
- Entities with no hygiene issues SHALL use INFO risk level with "Accepted" disposition.

#### Scenario: High-risk action includes explicit mitigation

- GIVEN stash@{0} contains 123K+ lines of uncommitted work
- WHEN the report recommends disposition
- THEN risk is HIGH, mitigation states "preserve first"
- AND "drop" is NOT listed as an option

#### Scenario: Medium-risk action for squash-merged branch

- GIVEN `origin/codex/graph-mvp` has PR #74 merged via GitHub squash
- WHEN the report recommends deletion
- THEN risk is MEDIUM, notes "code in main but commit history not preserved"
- AND rollback requires recorded tip SHA

#### Scenario: Low-risk action confirms full merge ancestry

- GIVEN `origin/feat/documentation-skill-phase1` has full ancestry in main
- WHEN the report recommends deletion
- THEN risk is LOW and verification confirms zero delta vs main

#### Scenario: INFO risk for accepted entity

- GIVEN tags have no hygiene issues
- WHEN the Tags entry is dispositioned
- THEN risk is INFO and disposition is "Accepted"

### Requirement: CI/CD and Tag Coverage

The report MUST include explicit dispositions for CI/CD configuration (security scan `continue-on-error`) and versioning tag strategy, even if no action is recommended.

#### Scenario: CI/CD configuration is reviewed

- GIVEN exploration identified `continue-on-error: true` on CodeQL and dependency review
- WHEN the report covers CI/CD
- THEN it documents the finding with INFO risk and an "Accepted" or "Review recommended" disposition

#### Scenario: Versioning tag strategy is documented

- GIVEN no `v*` tags exist in the repository
- WHEN the report covers Tags
- THEN it documents the absence with INFO risk and notes "no versioning via tags"

### Requirement: Rollback Plan

Every action that modifies git state MUST include a rollback command that restores the previous state.

Branch deletion rollback MUST record the tip SHA via `git rev-parse origin/{branch}` BEFORE deletion, then use `git push origin {recorded_sha}:refs/heads/{branch}` to restore. Config removal MUST document original content. Stash actions MUST NOT offer drop — only preserve or apply.

#### Scenario: Branch deletion records SHA before deletion

- GIVEN `origin/feat/documentation-skill-phase1` is targeted for deletion
- WHEN the action is executed
- THEN the tip SHA is recorded via `git rev-parse origin/feat/documentation-skill-phase1` first
- AND rollback uses `git push origin {sha}:refs/heads/feat/documentation-skill-phase1`

#### Scenario: Stash action has no drop option

- GIVEN stash@{0} is recommended for disposition
- WHEN the report lists actions
- THEN "drop" is NOT an option — only "apply to branch" or "document as frozen"

#### Scenario: Config removal documents original values

- GIVEN ghost config entries exist for deleted local branches
- WHEN config removal is executed
- THEN original key-value pairs are documented
- AND rollback restores them via `git config` commands

### Requirement: Completeness

The report MUST address all 9 exploration risks: author identity, stash, stale branches, ghost config, hook paths, dependabot staleness, CODEOWNERS, security scan config, versioning tags.

Entities with no action needed SHALL use "Accepted — no action needed" as the canonical disposition. No other terminology SHALL be used.

#### Scenario: All exploration risks are covered

- GIVEN the exploration identified 9 risks
- WHEN the report is reviewed
- THEN each risk has at least one action or an "Accepted — no action needed" declaration

#### Scenario: Open Items section covers both PRs and Issues

- GIVEN 6 open issues lack classification labels AND 1 stale PR (#85) exists
- WHEN the Open Items section is written
- THEN each issue is listed with age, current labels, and triage recommendation
- AND each stale PR is listed with closure recommendation

### Requirement: Actionability

Each action MUST be independently executable with: exact command(s), expected outcome, verification step, rollback command, and source traceability (exploration section reference).

#### Scenario: Action item is self-contained

- GIVEN a P1 action to clean ghost config entries
- WHEN the action is read
- THEN it contains: command, entries to remove, expected output, original values for rollback, and source reference to exploration §Stale Local Branch Config Entries

#### Scenario: Tags with hygiene issues produce prioritized actions

- GIVEN tags include outdated patterns or missing annotations
- WHEN the Tags section is written
- THEN each issue is classified by priority with actions and rollback commands
