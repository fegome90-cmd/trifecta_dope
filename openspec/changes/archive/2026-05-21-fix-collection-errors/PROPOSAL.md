# Proposal: fix-collection-errors

**Intent**: Restore full test suite collection (2014 tests) by fixing 3 broken test files and committing stale working tree changes.

**Scope**: 3 test files + 2 uncommitted test modifications.

**Approach**: Fix import paths for refactored modules, remove orphan test, fix daemon manager fixture, and commit pending changes.

## Problems

### P1: test_lsp_daemon.py — ImportError

- **What**: `from src.infrastructure.lsp_daemon import LSPDaemonClient` fails
- **Root cause**: Module was refactored from `src.infrastructure.lsp_daemon` to `src.infrastructure.daemon.client:DaemonClient`. Test still references old path.
- **Severity**: Blocks collection, 170-line integration test dead.

### P2: test_sanitizer.py — ImportError

- **What**: `from src.domain.sanitizer import Sanitizer` fails
- **Root cause**: `src.domain.sanitizer` module no longer exists. No `Sanitizer` class anywhere in codebase. Module was likely removed during a refactor.
- **Severity**: Blocks collection, 50-line orphan test with no corresponding source.

### P3: test_daemon_manager.py — 5 AssertionErrors

- **What**: All 5 tests fail with `Socket path blocked by non-socket file`
- **Root cause**: Stale socket files from previous daemon runs in `/var/folders/...` not cleaned up by test fixture. The `ALLOWED_BASES` fixture monkeypatches paths but doesn't ensure socket cleanup.
- **Severity**: Collection succeeds but all 5 tests fail.

### P4: Uncommitted working tree changes

- **What**: `test_idf_scoring.py` and `test_no_synthetics.py` modified but not committed (from recent IDF + synthetics work)
- **Root cause**: Tests were updated during search ranking fixes but not included in the commit
- **Severity**: Dirty working tree, changes at risk of loss.

## Non-goals

- Refactoring the daemon subsystem beyond fixing the test issues
- Changing the daemon manager architecture
- Re-implementing the Sanitizer class

## Rollback

Each fix is a separate atomic commit. Revert per-commit if needed.

## Owner

Single writer: parent session inline (mechanical fixes, no delegation needed).
