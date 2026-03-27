# Comprehensive Code Review: LSP + Daemon Subsystem

**Date**: 2026-03-26
**Review Type**: mr-comprehensive (7 agents)
**Segment**: trifecta_dope
**Duration**: ~5 minutes

---

## Executive Summary

7-agent comprehensive review of the LSP + Daemon subsystem identified **10 findings** across 5 files:

| Severity | Count | Action |
|----------|-------|--------|
| Critical | 2 | Fix immediately |
| Important | 5 | Fix before merge |
| Suggestion | 3 | Consider |

**Overall Assessment**: Code is well-structured with strong type safety and explicit fallback contracts. Main issues are resource management (file handle leak) and process lifecycle verification.

---

## Critical Issues (Confidence 75-100)

### CRIT-1: File Handle Leak in DaemonManager.start()

**Agent**: feature-dev:code-reviewer
**File**: `src/platform/daemon_manager.py`
**Lines**: 68-97
**Confidence**: 95/100

**Description**: The `log_file` handle opened at line 68 is never closed. While Python's GC will eventually close it, relying on GC for file handles is a resource leak. Sequential restarts could accumulate leaked handles.

**Evidence**:
```python
log_file = self._log_path.open("a")  # Line 68 - opened but never closed
proc = subprocess.Popen(
    [python_exe, str(cli_path), "daemon", "run"],
    ...
    stdout=log_file,  # Passed to subprocess
)
# log_file is never explicitly closed
```

**Suggested Fix**:
```python
log_file = self._log_path.open("a")
try:
    proc = subprocess.Popen(..., stdout=log_file, ...)
finally:
    # subprocess has its own fd reference, we can close our handle
    log_file.close()
```

---

### CRIT-2: Race Condition - PID Written Before Process Verified Alive

**Agent**: feature-dev:code-reviewer
**File**: `src/platform/daemon_manager.py`
**Lines**: 89-94
**Confidence**: 85/100

**Description**: The PID file is written immediately after socket exists, but the process could have crashed between spawn and socket creation. If the daemon crashes after creating the socket, the PID file contains a dead PID.

**Evidence**:
```python
for _ in range(self.DAEMON_START_TIMEOUT * 10):
    if self._socket_path.exists():
        self._pid_path.write_text(str(proc.pid))  # PID written without verifying alive
        return True
```

**Suggested Fix**:
```python
for _ in range(self.DAEMON_START_TIMEOUT * 10):
    if self._socket_path.exists():
        if proc.poll() is None:  # Verify process still alive
            self._pid_path.write_text(str(proc.pid))
            return True
        else:
            return False  # Process exited, don't write stale PID
```

---

## Important Issues (Confidence 50-74)

### IMP-1: Clean Architecture Violation

**Agent**: pr-review-toolkit:code-reviewer
**File**: `src/application/daemon_use_case.py`
**Lines**: 4-5
**Confidence**: 95/100

**Description**: The application layer imports directly from the platform layer. This violates Clean Architecture's dependency rule where dependencies must point inward.

**Evidence**:
```python
from src.platform.daemon_manager import DaemonManager
from src.platform.health import HealthChecker
```

**Suggested Fix**: Define abstract protocols in domain layer:
```python
# In src/domain/daemon_contracts.py
from typing import Protocol

class DaemonOperations(Protocol):
    def start(self) -> bool: ...
    def stop(self) -> bool: ...
    def restart(self) -> bool: ...
    def status(self) -> DaemonStatus: ...
```

---

### IMP-2: Malformed Docstring in daemon_paths.py

**Agent**: feature-dev:code-reviewer
**File**: `src/infrastructure/daemon_paths.py`
**Lines**: 16-23
**Confidence**: 100/100

**Description**: The docstring for `_validate_daemon_base_dir` has malformed Raises section.

**Evidence**:
```python
def _validate_daemon_base_dir(tmp_dir: Path) -> None:
    """
        Validate that base directory for daemon files is accessible.

        Raises:
            Runtime

    Error: If tmp_dir doesn't exist or isn't writable.
    """
```

**Suggested Fix**:
```python
def _validate_daemon_base_dir(tmp_dir: Path) -> None:
    """
    Validate that base directory for daemon files is accessible.

    Raises:
        RuntimeError: If tmp_dir doesn't exist or isn't writable.
    """
```

---

### IMP-3: Misplaced Docstring in lsp_client.py

**Agent**: feature-dev:code-reviewer
**File**: `src/infrastructure/lsp_client.py`
**Lines**: 453-465
**Confidence**: 85/100

**Description**: The docstring appears after timeout calculation logic, indicating a merge/reorder error.

**Evidence**:
```python
def request(
    self, method: str, params: Dict[str, Any], timeout: float | None = None
) -> Optional[Dict[str, Any]]:
    if timeout is None:
        env_timeout = os.environ.get("TRIFECTA_LSP_REQUEST_TIMEOUT")
        ...
    """Send a request and wait for the response."""  # <-- Wrong position
    with self.lock:
```

**Suggested Fix**: Move docstring to immediately after function definition.

---

### IMP-4: Missing Type Annotation for _lock_fp

**Agent**: feature-dev:code-reviewer
**File**: `src/infrastructure/lsp_daemon.py`
**Lines**: 49
**Confidence**: 90/100

**Description**: The `_lock_fp` attribute is typed as `Any` but should be `Optional[TextIO]`.

**Evidence**:
```python
self._lock_fp: Any = None
```

**Suggested Fix**:
```python
from typing import TextIO
# ...
self._lock_fp: Optional[TextIO] = None
```

---

### IMP-5: Inconsistent Cleanup in DaemonManager.stop()

**Agent**: feature-dev:code-reviewer
**File**: `src/platform/daemon_manager.py`
**Lines**: 99-115
**Confidence**: 82/100

**Description**: Files are cleaned even if daemon process survives kill, potentially leaving an orphaned daemon.

**Evidence**:
```python
def stop(self) -> bool:
    ...
    finally:
        self._cleanup_files()  # Always cleans files, even if kill failed
```

**Suggested Fix**: Only cleanup if process is confirmed dead:
```python
finally:
    if not self._is_process_alive(pid):
        self._cleanup_files()
```

---

## Suggestions (Confidence 25-49)

### SUG-1: Dead Code - Deprecated LSPManager

**Agent**: pr-review-toolkit:code-simplifier
**File**: `src/application/lsp_manager.py`
**Lines**: 1-255
**Confidence**: 100/100

**Description**: The file header explicitly marks this as deprecated. The `request_definition()` method always returns `None` (MVP stub). This is 255 lines of non-operational code.

**Recommendation**: Remove or move to `_deprecated/` directory if reference is needed.

---

### SUG-2: Missing Test Coverage for LSPClient.start()

**Agent**: pr-review-toolkit:pr-test-analyzer
**File**: `tests/unit/test_lsp_client_strict.py`
**Confidence**: 85/100

**Description**: No unit tests for `start()` method failure scenarios:
- Binary not found (`shutil.which` returns None)
- `subprocess.Popen` exception handling
- Process spawn failure with stderr capture

**Recommendation**: Add unit tests for error paths.

---

### SUG-3: Redundant Protocol in runtime_manager.py

**Agent**: pr-review-toolkit:code-simplifier
**File**: `src/platform/runtime_manager.py`
**Confidence**: 70/100

**Description**: Defines `DaemonManager` protocol that duplicates the concrete class interface.

**Recommendation**: Consolidate or remove redundant abstraction.

---

## Strengths (Positive Findings)

| Area | Observation | Agent |
|------|-------------|-------|
| State Machine | `LSPState` transitions well-designed with proper locking | code-reviewer |
| Singleton Lock | Socket-based lock with stale recovery is robust | code-reviewer |
| TTL Implementation | Proper timeout handling with activity tracking | code-reviewer |
| Explicit Fallback | `LSPResponse` contract makes degraded behavior observable | code-reviewer |
| Test Patterns | Integration tests use polling instead of `sleep` | test-analyzer |
| Type Checking | Passes strict mypy without errors | code-reviewer |
| Linting | All ruff checks pass | code-reviewer |
| Invariant Tracking | `_failed_invariants` list provides diagnostics | type-design-analyzer |
| Error Propagation | `_emit_fallback()` makes AST fallback explicit | silent-failure-hunter |

---

## Test Coverage Analysis

### Covered

| Scenario | Test File |
|----------|-----------|
| Daemon start/stop lifecycle | `test_daemon_manager.py` |
| Singleton lock semantics | `test_daemon_manager.py` |
| TTL-based shutdown | `test_lsp_daemon.py` |
| LSP contract fallback | `test_lsp_contract_fallback.py` |
| Strict LSP client behavior | `test_lsp_client_strict.py` |

### Missing Coverage

| Scenario | Criticality |
|----------|-------------|
| `LSPClient.start()` binary not found | High |
| `LSPClient.start()` subprocess exception | High |
| Process spawn failure with stderr | Medium |
| State transition edge cases | Medium |
| Concurrent access patterns | Low |

---

## Silent Failure Analysis

### Findings

| Pattern | Location | Status |
|---------|----------|--------|
| `except Exception: pass` | `lsp_daemon.py:251` | Acceptable (shutdown cleanup) |
| Bare `except Exception` | `lsp_client.py:110-114` | Logged to stderr (acceptable) |
| Timeout without logging | `lsp_client.py:442` | Has `_emit_fallback()` ✓ |

### Verdict

No silent failures detected. All fallback paths emit telemetry via `_emit_fallback()`.

---

## Type Design Analysis

### LSPResponse (dataclass)

| Invariant | Status |
|-----------|--------|
| Status consistency | ✅ Enforced via factory methods |
| Immutability | ✅ `@dataclass` without setters |
| Fallback reason required if degraded | ⚠️ Not enforced at type level |

### LSPState (enum)

| Aspect | Status |
|--------|--------|
| Valid transitions | ✅ Clear in code |
| Thread-safe state changes | ✅ Uses `threading.Lock` |
| Exhaustive handling | ✅ All states handled in `_run_loop` |

### FallbackReason (enum)

| Aspect | Status |
|--------|--------|
| Coverage of failure modes | ✅ Comprehensive |
| Extensibility | ✅ Easy to add new reasons |

---

## Files Reviewed

| File | Lines | Purpose |
|------|-------|---------|
| `src/platform/daemon_manager.py` | 189 | Official daemon surface |
| `src/infrastructure/lsp_client.py` | 560 | LSP client with state machine |
| `src/domain/lsp_contracts.py` | 167 | Domain contracts |
| `src/infrastructure/daemon_paths.py` | 104 | Path utilities |
| `src/application/daemon_use_case.py` | 35 | Use case layer |
| `src/infrastructure/daemon/lsp_handler.py` | 100 | LSP request handler |
| `src/platform/health.py` | 50 | Health checker |
| `tests/unit/test_daemon_manager.py` | 78 | Unit tests |
| `tests/integration/test_lsp_daemon.py` | 171 | Integration tests |

---

## Verification Commands

```bash
# Run tests
uv run pytest tests/unit/test_daemon_manager.py tests/integration/test_lsp_daemon.py -v

# Type checking
uv run mypy src/platform/daemon_manager.py src/infrastructure/lsp_client.py --strict

# Linting
uv run ruff check src/platform/ src/infrastructure/lsp*.py src/infrastructure/daemon*.py
```

---

## Recommended Actions

1. **Immediate**: Fix CRIT-1 (file handle leak) and CRIT-2 (race condition)
2. **Before merge**: Fix IMP-1 through IMP-5
3. **Consider**: Remove deprecated `lsp_manager.py` (SUG-1)
4. **Future**: Add test coverage for `LSPClient.start()` error paths

---

## Session Log

```
trifecta session append --segment . --summary "mr-comprehensive LSP+Daemon completado" --files "daemon_manager.py,lsp_client.py,lsp_contracts.py,daemon_paths.py,daemon_use_case.py" --commands "mr-comprehensive,7-agent-review"
```

---

*Generated by mr-comprehensive (7-agent review) on 2026-03-26*
