# Tasks: fix-collection-errors

## Phase 1: Cleanup and path fixes

### T1.1: Delete orphan test_sanitizer.py

- **REQ**: REQ-02
- **Action**: Delete `tests/unit/test_sanitizer.py`
- **Verify**: `uv run pytest --co -q 2>&1 | grep test_sanitizer` returns nothing

### T1.2: Fix test_lsp_daemon.py imports and subprocess paths

- **REQ**: REQ-01
- **Action**:
  1. Replace `from src.infrastructure.lsp_daemon import LSPDaemonClient` → `from src.infrastructure.daemon.client import DaemonClient`
  2. Replace all references to `LSPDaemonClient` → `DaemonClient`
  3. Update subprocess commands: `src.infrastructure.lsp_daemon` → `src.infrastructure.daemon.runner`
  4. Keep `daemon_paths` and `helpers` imports unchanged
- **Verify**: `uv run pytest tests/integration/test_lsp_daemon.py --co` collects without errors

### T1.3: Fix test_daemon_manager.py assertions and fixture

- **REQ**: REQ-03
- **Action**:
  1. Update `allowed_runtime` fixture to clean stale socket/lock files before yielding
  2. Fix `assert manager.start() is False` → tuple-compatible assertion
  3. Fix `assert started is True` → tuple-compatible assertion
  4. Ensure fixture also removes socket file that causes "Socket path blocked by non-socket file"
- **Verify**: `uv run pytest tests/unit/test_daemon_manager.py -v` — all 5 pass

## Phase 2: Commit

### T2.1: Commit pending IDF/synthetics test changes

- **REQ**: REQ-04
- **Action**: `git add tests/unit/test_idf_scoring.py tests/unit/test_no_synthetics.py` and commit
- **Verify**: `git status` shows both files clean

### T2.2: Commit collection fixes

- **REQ**: REQ-01, REQ-02, REQ-03
- **Action**: Stage and commit each fix atomically
- **Verify**: `uv run pytest --co -q` shows 0 errors

## Verification Gate

- `uv run pytest --co -q` → 0 collection errors
- `uv run pytest tests/unit/test_daemon_manager.py -v` → 5/5 pass
- `uv run pytest tests/ -x` → no regressions (tests that were passing before still pass)
