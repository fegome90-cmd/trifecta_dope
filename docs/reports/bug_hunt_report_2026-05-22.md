# Bug Hunt Report — trifecta CLI — 2026-05-22

## Executive Summary

- Agents deployed: ripper (adversarial), walker (workflows), sniper (isolation)
- Subsystems tested: ctx (search/get/oracle/build/reset), query, index, graph, daemon, telemetry
- Total findings: 6 (0 CRITICAL, 2 HIGH, 2 MEDIUM, 2 LOW)
- Verdict: **PASS WITH WARNINGS**

---

## Findings by Severity

### HIGH

| ID  | Title                                                  | Subsystem | Agent         | User Trigger? | Command                                     | Expected                             | Actual                                                             |
| --- | ------------------------------------------------------ | --------- | ------------- | ------------- | ------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------ |
| H1  | Daemon starts for arbitrary path outside allowed bases | daemon    | ripper        | YES           | `trifecta daemon start -r "/tmp/../../etc"` | Rejected — path not in ALLOWED_BASES | "Daemon started" with active PID                                   |
| H2  | Query index crawls .worktrees (stale branches indexed) | query     | walker+sniper | MAYBE         | `trifecta query -r . "daemon" --json`       | Results from main repo only          | Results include .worktrees/codex-\* branches (stale deleted files) |

### MEDIUM

| ID  | Title                                              | Subsystem | Agent  | User Trigger? | Command                                                       | Expected                                            | Actual                                                                             |
| --- | -------------------------------------------------- | --------- | ------ | ------------- | ------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| M1  | ctx reset --force destructive without confirmation | ctx       | walker | YES           | `trifecta ctx reset -s . --force`                             | Confirmation prompt or at least warning about scope | Silently regenerates all templates and rebuilds pack                               |
| M2  | Graph callers silently fails on ambiguous symbols  | graph     | walker | YES           | `trifecta graph callers --symbol "DaemonManager" -s . --json` | Disambiguation help or top-match selection          | Returns `ok: false` with GRAPH_TARGET_AMBIGUOUS error — no fallback, no suggestion |

### LOW

| ID  | Title                                          | Subsystem | Agent  | User Trigger? | Command                                                 | Expected                | Actual                                                          |
| --- | ---------------------------------------------- | --------- | ------ | ------------- | ------------------------------------------------------- | ----------------------- | --------------------------------------------------------------- |
| L1  | Oracle returns fallback for relational queries | oracle    | walker | YES           | `trifecta ctx oracle -q "who calls DaemonManager" -s .` | graph_data with callers | fidelity=fallback, graph_data=null (graph signal stale/timeout) |
| L2  | ctx get returns empty for valid IDs            | ctx       | walker | MAYBE         | `trifecta ctx get -s . --ids <valid-id>`                | Returns chunk content   | 0 chunks retrieved (ID format mismatch between search and get)  |

### INFO

| ID  | Title                                                              | Notes                                                                                                           |
| --- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| I1  | CLI error messages suggest wrong flags                             | `trifecta ctx search` errors suggest `-r` instead of `-s`/`-q`. Help UX is inconsistent between commands.       |
| I2  | Query index includes 1843 files but context pack is segment-scoped | index and ctx operate on different scopes — index is repo-wide, ctx is segment-scoped. Not a bug but confusing. |

---

## Key Finding Details

### H1: Daemon starts for arbitrary path outside ALLOWED_BASES

- **Reproduce**: `trifecta daemon start -r "/tmp/../../etc"` → "Daemon started"
- **Root cause**: `DaemonManager` accepts any repo_root, derives fingerprint, creates runtime dirs. The ALLOWED_BASES guard in `is_runtime_dir_allowed` is checked for runtime_dir but NOT for the repo_root passed to `daemon start`.
- **Impact**: A user can accidentally start daemon processes for arbitrary directories, creating socket/PID files in temp dirs. In CI/CD, this could lead to resource leaks.
- **Fix**: Add repo_root validation in `trifecta daemon start` command before creating DaemonManager.

### H2: Query index crawls .worktrees

- **Reproduce**: `trifecta index -r . --json` → 1843 files indexed. Results include files from `.worktrees/codex-checkpoint-gate/`, `.worktrees/codex-graph-mvp/` etc.
- **Root cause**: The file walker in index doesn't exclude `.worktrees/` directory.
- **Impact**: Stale branches inflate index, return duplicate/stale results, confuse search ranking.
- **Fix**: Add `.worktrees/` to exclusion list in the file walker (alongside `.git/`, `node_modules/`, etc.)

---

## Agent Coverage Matrix

| Subsystem  | Ripper | Walker | Sniper | Coverage |
| ---------- | ------ | ------ | ------ | -------- |
| ctx search | ✓      | ✓      | ✓      | Full     |
| ctx get    | ✓      | ✓      | -      | Partial  |
| ctx build  | -      | ✓      | -      | Basic    |
| ctx reset  | ✓      | ✓      | -      | Basic    |
| ctx oracle | ✓      | ✓      | -      | Partial  |
| query      | ✓      | ✓      | ✓      | Full     |
| index      | -      | ✓      | -      | Basic    |
| daemon     | ✓      | ✓      | ✓      | Full     |
| graph      | ✓      | ✓      | -      | Partial  |
| telemetry  | -      | -      | ✓      | Basic    |

---

## Positives (Security Done Right)

1. **SQL injection**: `'; DROP TABLE` in search → handled safely, returns results (FTS5 parameterized)
2. **Shell injection**: `$(cat /etc/passwd)` → shell-expanded before CLI sees it, but search handles safely
3. **Empty query**: Rejected with clear error message
4. **Path traversal in ctx build**: Caught and rejected with clear error
5. **Template injection**: `{{7*7}}` treated as literal text — no evaluation
6. **Unicode RTL**: Handled gracefully, returns "No results"
7. **Very long query**: Handled gracefully, returns "No results" without crash
8. **Daemon isolation**: Different segments don't see each other's daemons
9. **Telemetry isolation**: Export scoped to segment, no cross-segment data
10. **Worktrees not in context pack**: ctx build correctly excludes .worktrees
11. **Git directory excluded**: query index doesn't include .git files
