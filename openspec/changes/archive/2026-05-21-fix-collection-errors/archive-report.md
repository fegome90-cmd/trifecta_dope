# Archive Report: fix-collection-errors

**Date**: 2026-05-21
**Verdict**: PASS WITH WARNINGS
**Commits**: 5cce031c, 6391d651, 01d3736e

## Summary

Fixed 3 test collection errors blocking the 2019-test suite:

1. Deleted orphan `test_sanitizer.py` (module `src.domain.sanitizer` removed)
2. Deleted `test_lsp_daemon.py` (API `LSPDaemonClient` replaced by `DaemonClient` + `DaemonRunner`)
3. Realigned `test_daemon_manager.py` (tuple return type, lock path, stale cleanup)

Also fixed 7 additional failures in `tests/integration/daemon/test_daemon_manager.py` and committed 2 pending test files from IDF/synthetics work.

## Delta Specs Merged

None — test fix change, no domain spec modifications.

## Files Changed

| File                                              | Action                                        |
| ------------------------------------------------- | --------------------------------------------- |
| `tests/unit/test_sanitizer.py`                    | Deleted                                       |
| `tests/integration/test_lsp_daemon.py`            | Deleted                                       |
| `tests/unit/test_daemon_manager_unit.py`          | Created (renamed from test_daemon_manager.py) |
| `tests/integration/daemon/test_daemon_manager.py` | Rewritten                                     |
| `src/platform/daemon_manager.py`                  | 1 line fix (restart() return type)            |
| `tests/unit/test_idf_scoring.py`                  | Committed (pending changes)                   |
| `tests/unit/test_no_synthetics.py`                | Committed (pending changes)                   |

## Known Issues Carried Forward

- 79 preexisting test failures (validators, strict_validation, t7, acceptance)
- `test_vague_spanish_query_on_hits_via_expansion` broken by d96cee56
- Oracle LSP not wired (Nivel 2 backlog)
- Graph stale >7 days
