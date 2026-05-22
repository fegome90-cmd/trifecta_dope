# Spec: fix-collection-errors

## Requirements

### REQ-01: test_lsp_daemon.py removal (API generation gap)

- **Given** the daemon was fully refactored: `LSPDaemonClient` (old API with `connect_or_spawn`, `_try_connect`) no longer exists and was replaced by `DaemonClient(socket_path)` + `DaemonRunner`
- **And** the test uses `python -m src.infrastructure.lsp_daemon` subprocess calls that have no equivalent in the new architecture
- **And** the new API (`DaemonClient`, `DaemonRunner`) has no integration tests yet (Nivel 2 work)
- **When** pytest collects the test suite
- **Then** `tests/integration/test_lsp_daemon.py` SHALL be deleted
- **And** collection SHALL succeed with 0 errors
- **Note**: Re-writing integration tests for the new daemon API is out of scope (Nivel 2 — Oracle LSP wiring)

### REQ-02: test_sanitizer.py orphan removal

- **Given** `src.domain.sanitizer` module no longer exists anywhere in the codebase
- **When** pytest collects the test suite
- **Then** `tests/unit/test_sanitizer.py` SHALL be deleted
- **And** collection SHALL succeed with 0 errors
- **Note**: The file contains 5 test methods (50 lines total including helpers), not 50 tests

### REQ-03: test_daemon_manager.py realignment with refactored DaemonManager

- **Given** `DaemonManager.start()` returns `tuple[bool, Optional[str]]` (not `bool`)
- **And** `DaemonManager` lock path moved from `{socket_path}.lock` to `get_daemon_lock_path(fp)` (`trifecta_lsp_{fp}.lock`, not `.sock.lock`)
- **And** `_acquire_singleton_lock()` now uses `_lock_path` (not `_socket_path + ".lock"`) and has a different flow with `_lock_owner_is_alive`, `_wait_for_lock_release`
- **And** `_socket_path` and `_lock_path` are derived from fingerprint of repo_root (global temp paths, not test-local)
- **When** `test_daemon_manager.py` runs
- **Then** all assertions SHALL be updated:
  1. `start()` return type: unpack tuple, e.g. `started, msg = manager.start()`
  2. Lock path: use `manager._lock_path` instead of `Path(str(manager._socket_path) + ".lock")`
  3. Singleton lock flow: re-align with current `_acquire_singleton_lock()` implementation
  4. Socket stale cleanup: fixture SHALL remove stale files at `manager._socket_path` and `manager._lock_path` before yielding
- **And** all 5 tests in `test_daemon_manager.py` SHALL pass

### REQ-04: Commit pending test modifications

- **Given** `tests/unit/test_idf_scoring.py` and `tests/unit/test_no_synthetics.py` contain uncommitted changes from the IDF/synthetics work
- **When** this change is applied
- **Then** the modified test files SHALL be committed as part of the fix

## Scenarios

### Scenario S01: Full suite collection

- **Given** all 4 fixes applied
- **When** `uv run pytest --co -q` runs
- **Then** collection SHALL complete with 0 errors
- **And** total test count SHALL be >= 2004 (2014 minus 5 sanitizer tests minus 5 lsp_daemon tests)

### Scenario S02: Daemon manager tests pass

- **Given** REQ-03 applied
- **When** `uv run pytest tests/unit/test_daemon_manager.py -v`
- **Then** all 5 tests SHALL pass

### Scenario S03: No regressions in passing tests

- **Given** all 4 fixes applied
- **When** `uv run pytest tests/ -x` runs the full suite (including fixed files)
- **Then** no previously passing test SHALL fail

## Invariants

- INV-01: No production source code SHALL be modified — only test files and orphan removal
- INV-02: No new dependencies SHALL be introduced
- INV-03: Each fix SHALL be a separate atomic commit
