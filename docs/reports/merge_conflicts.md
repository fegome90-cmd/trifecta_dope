# Merge Conflict Decisions

## Context

This report lists the dirty files in `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope` at the time of merge. The authoritative version is the merge worktree at `/Users/felipe_gonzalez/Developer/agent_h/wt-merge-backlog-wo`. Each entry records whether we keep the merge worktree version or explicitly incorporate content from the dirty main worktree.

## Decisions

- `.coverage`: ignored (local artifact). Keep merge worktree; do not merge.
- `.github/workflows/ci.yml`: keep merge worktree version.
- `_ctx/context_pack.json`: ignore (local context pack). Keep merge worktree.
- `_ctx/generated/repo_map.md`: ignore (generated). Keep merge worktree.
- `_ctx/generated/symbols_stub.md`: ignore (generated). Keep merge worktree.
- `_ctx/telemetry/events.jsonl`: ignore (telemetry). Keep merge worktree.
- `_ctx/telemetry/last_run.json`: ignore (telemetry). Keep merge worktree.
- `docs/CONTRACTS.md`: keep merge worktree version.
- `docs/reports/merge_readiness_ast_cache_audit_grade.md`: keep merge worktree version.
- `src/application/ast_parser.py`: keep merge worktree version.
- `src/domain/ast_cache.py`: keep merge worktree version.
- `src/infrastructure/cli_ast.py`: keep merge worktree version.
- `tests/acceptance/test_pd_evidence_stop_e2e.py`: keep merge worktree version.
