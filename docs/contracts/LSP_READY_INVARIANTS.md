# LSP READY Invariants Contract

## Overview

This contract defines the **invariant checks** that MUST pass before the `LSPClient` can transition to the `READY` state. This ensures that `READY` truly means "operational and capable of serving requests."

## Problem

The previous "relaxed READY" contract (see `LSP_RELAXED_READY.md`) only verified that the LSP handshake completed. This meant `READY` could be reported even when:
- The LSP process had crashed
- The workspace root was incorrect
- The LSP was not responding to requests

## Invariants

Before transitioning to `READY`, the following invariants MUST all pass:

### 1. Handshake Complete (`handshake_complete`)
- `initialize` request must return a successful response
- `initialized` notification must be sent
- At least empty capabilities must be received

### 2. Process Alive (`process_alive`)
- The LSP subprocess must be running (not terminated)
- `process.poll()` must return `None`

### 3. Workspace Root Correct (`workspace_root_correct`)
- `root_path` must be set and must exist on the filesystem
- The path must be accessible for file operations

### 4. Health Check Responds (`health_check_responds`)
- The LSP must have returned capabilities from the handshake
- This indicates the server is capable of processing requests

## Implementation

### Invariant Tracking

Failed invariants are tracked in `LSPClient._failed_invariants`:
```python
INVARIANT_HANDSHAKE = "handshake_complete"
INVARIANT_PROCESS_ALIVE = "process_alive"
INVARIANT_WORKSPACE_ROOT = "workspace_root_correct"
INVARIANT_HEALTH_CHECK = "health_check_responds"
```

### State Transition

```python
def _run_loop(self) -> None:
    # ... handshake ...
    
    if not self._check_invariants():
        self._log_event(
            "lsp.state_change",
            {},
            {"status": "failed", "reason": "invariant_check_failed"},
            1,
            reason="invariant_check_failed",
            failed_invariants=",".join(self._failed_invariants),
        )
        self._transition(LSPState.FAILED)
        return
    
    self._transition(LSPState.READY)
```

### Health Check API

```python
def health_check(self, timeout_ms: int = 500) -> bool:
    """Verify LSP can respond within timeout."""
    if self.state != LSPState.READY:
        return False
    
    result = self.request("$/health", {}, timeout=timeout_ms / 1000.0)
    return result is not None
```

## Telemetry Events

### lsp.state_change (on transition failure)
```python
{
    "cmd": "lsp.state_change",
    "result": {"status": "failed", "reason": "invariant_check_failed"},
    "reason": "invariant_check_failed",
    "failed_invariants": "process_alive,workspace_root_correct"
}
```

### lsp.health_check
```python
{
    "cmd": "lsp.health_check",
    "result": {"status": "timeout", "latency_ms": 523},
    "timing": 523
}
```

## Verification

Tests verifying this contract:
- `tests/integration/test_ready_semantics_documented_and_enforced.py::test_ready_semantics_is_post_initialize`
- `tests/integration/test_ready_semantics_documented_and_enforced.py::test_ready_fails_when_invariants_fail`
- `tests/integration/test_ready_semantics_documented_and_enforced.py::test_invariant_check_tracks_failures`
