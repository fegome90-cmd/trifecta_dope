# ADR: Finish Gate Policy - Origin/Main + Merge-Base + Unknown Blocks

**Date**: 2026-02-15
**Status**: Accepted
**WO**: WO-0047
**PR**: #41

## Context

The `ctx_wo_finish.py` script generates diff.patch for handoff but had three critical vulnerabilities:
1. Unknown `_ctx/` paths passed silently (fail-open)
2. Used fragile local `main` as base branch
3. Diff range was ambiguous (could miss merge history)

## Decision

We implemented three hardening rules:

1. **Fail-closed unknown paths**: Any `_ctx/` path not in `ignore` or `allowlist_contract` **blocks** finish with actionable error
2. **Robust base branch**: `git fetch origin` + `origin/main` (not local `main`)
3. **Merge-base diff**: `git diff --merge-base origin/main HEAD` (handles history correctly)

## Policy Scope

- Policy filtering applies **only to `_ctx/` paths**
- Non-`_ctx/` paths (src/, tests/) are always allowed
- Policy file: `_ctx/policy/ctx_finish_ignore.yaml`

## Consequences

- **Positive**: No silent drift of `_ctx/` state; diff always reflects true changes
- **Negative**: WOs must explicitly classify any new `_ctx/` paths in policy

## Review Cycle

This ADR should be reviewed when:
- New `_ctx/` subdirectories are added
- The WO system is extended to other directories
