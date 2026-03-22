# Debt Track: `_ctx` and Hook State Outside Graph MVP

## Problem Observed

This worktree has a separate `_ctx` and hook-state problem that can interfere with context-related flows:

- `_ctx` metadata in the worktree is not consistently aligned with the `codex-graph-mvp` segment suffix expectations
- context-related hooks can fail when `_ctx` files are staged or when `ctx sync` is forced through the worktree-local state

## Why This Is Not Part of Graph MVP

The Graph MVP is a CLI feature in the `graph` namespace. Its acceptance scope is:

- AST-only indexing
- SQLite-only storage
- graph navigation commands
- explicit runtime contracts

The `_ctx` inconsistency is repository/worktree infrastructure debt. It is not caused by the Graph namespace and should not gate the Graph feature merge.

## Impact

- Graph code and tests can be clean and merge-ready while `_ctx` remains dirty or structurally inconsistent
- staging `_ctx` files may trigger hook paths unrelated to the Graph feature itself
- feature closure and merge preparation should avoid mixing `_ctx` fixes with Graph scope

## Recommended Next Action

Handle `_ctx` as a separate debt item after the Graph MVP merges:

1. audit the worktree-local `_ctx` naming and expected suffixes
2. reproduce the hook failure independently of Graph changes
3. define the ownership boundary between feature worktrees and context/hook infrastructure
4. fix and verify `_ctx`/hook behavior in a dedicated batch

## Current Decision

No `_ctx` fix is included in the Graph MVP merge-closeout batch.
