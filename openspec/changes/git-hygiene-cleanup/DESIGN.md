# Design: git-hygiene-cleanup

No architectural decisions — operational cleanup. Key design choices:

## DEC-01: Re-validation gate (REQ-01) before destructive ops

**Chosen**: Run `git fetch --prune` and re-check all branch/PR/CI states live.

**Why**: The audit data is from this session. Between audit and execution, someone could merge a PR, push to a branch, or CI could pass. Blind deletion based on stale data risks losing work.

**Implementation**: REQ-01 is a hard gate — if re-validation fails for any target, that target is skipped.

## DEC-02: Close Dependabot PRs vs merge

**Chosen**: Close with explanatory comment.

**Why**: Both PRs have failing CI (Lint, Security, Tests). The CI failures are preexisting (not caused by bumps). After push and stabilization, Dependabot will auto-create fresh PRs against current main with resolved conflicts.

## DEC-03: Preserve hygiene branches

**Chosen**: Do not delete `hygiene/git-audit-20260504` or `hygiene/stash-preserve-codex-freeze`.

**Why**:

- `git-audit-20260504` has 7 unique commits of audit documentation (hygiene/\*.md reports, SHA registry)
- `stash-preserve-codex-freeze` has a full repo snapshot including deleted source files (`src/domain/sanitizer.py`)
- Cost of keeping: zero (just remote refs)
- Cost of deleting: loss of historical recovery point

## DEC-04: GC last, not first

**Chosen**: GC runs after all ref deletions, stash drop, and tag cleanup.

**Why**: `git gc --prune=now` removes unreachable objects. If run before stash drop, it could prune objects the stash still references. If run before branch/tag deletion, those refs keep objects alive and GC is less effective.

## Dependency

This change depends on `publish-main-backlog` completing first:

- origin/main must be current before closing PRs (they reference main)
- stash content was verified against main — push ensures origin matches local verification
