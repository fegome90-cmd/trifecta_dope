# Daemon Drift Code Audit

**Date:** 2026-03-26  
**Skill selected via `skill-hub`:** `code-review-agent`  
**Why:** it is the best fit for analyzing recent code drift, identifying regressions/bugs, and producing a structured report with file paths, line references, consequences, logs, and test coverage.

## Scope audited

Changed files reviewed:
- `src/infrastructure/daemon/lsp_handler.py`
- `src/infrastructure/lsp_client.py`
- `src/platform/daemon_manager.py`
- `tests/unit/daemon/test_lsp_handler.py`
- `tests/unit/daemon/test_lsp_handler_didopen_format.py`
- `tests/unit/test_lsp_ready_contract.py`
- `tests/integration/test_ready_semantics_documented_and_enforced.py`

Focused validation executed:
```bash
uv run pytest tests/unit/daemon/test_lsp_handler.py tests/unit/daemon/test_lsp_handler_didopen_format.py tests/unit/test_lsp_ready_contract.py tests/integration/test_ready_semantics_documented_and_enforced.py -v
```

Result:
- `12 passed`

---

## Executive summary

There are **4 relevant code-level issues** in the current drift over the validated daemon batch:

1. **Silent success for LSP notifications**
2. **Production debug logging left enabled**
3. **Observable semantic change for `FAILED` state**
4. **Timeout configuration added without a full contract/test story**

The most important one is **#1** because it can report success even when no notification was actually delivered.

---

## Findings

### 1. Silent success in notification path

**Severity:** Critical  
**File:** `src/infrastructure/daemon/lsp_handler.py`  
**Lines:** `44-70` (notification branch), especially `69-70`  

**Evidence**
- `src/infrastructure/daemon/lsp_handler.py:44-70`
- `src/infrastructure/daemon/lsp_handler.py:69` calls `lsp_client._send_rpc(msg)`
- `src/infrastructure/daemon/lsp_handler.py:70` returns `LSPResponse.full_response({"status": "notification_sent"})`
- `src/infrastructure/lsp_client.py:535-545` shows `_send_rpc()` can no-op if:
  - `self.stopping.is_set()`
  - `not self.process`
  - `not self.process.stdin`
- `src/infrastructure/lsp_client.py:545-551` swallows `OSError`, `ValueError`, `BrokenPipeError`

**Problem**
The handler reports `notification_sent` as a successful full response even though `_send_rpc()`:
- does not return a success value,
- may silently do nothing,
- may swallow transport errors.

This means the daemon can claim success for `didOpen`/other notifications without proof that the notification actually left the process.

**Consequences**
- false-positive success responses
- harder debugging when pyright never receives the notification
- contract drift between observable API and real transport state
- possible masking of broken `stdin` / stopped process conditions

**Do we have logs to identify it?**
- **Partially / insufficiently**
- We do have daemon log redirection because `DaemonManager.start()` launches the daemon with:
  - `stdout=log_file`
  - `stderr=subprocess.STDOUT`
  - file path rooted at runtime daemon log (`src/platform/daemon_manager.py:74-87`)
- However, for this specific notification path there is **no authoritative success/failure log** tied to `_send_rpc()`.
- Therefore logs do **not** reliably prove whether `notification_sent` means “actually sent”.

**Do we have tests to prove it?**
- **We have partial tests only**
- Present:
  - `tests/unit/daemon/test_lsp_handler_didopen_format.py:19-47`
  - `tests/unit/daemon/test_lsp_handler_didopen_format.py:49-71`
- These prove:
  - parameter transformation is correct
  - `_send_rpc` is called
  - returned response says `notification_sent`
- Missing:
  - test where `_send_rpc` silently no-ops and handler still claims success
  - test where process/stdin is unavailable
  - test where transport failure should surface as degraded/error instead of false success

**Recommended next test**
- Add a unit test where a fake client has `_send_rpc()` that does nothing / simulates unavailable transport while `handle_lsp_request()` currently returns success.
- Decide intended contract: boolean confirmation, explicit error, or degraded response.

---

### 2. Production debug logging left enabled

**Severity:** Major  
**Files:**
- `src/infrastructure/daemon/lsp_handler.py`
- `src/infrastructure/lsp_client.py`

**Lines**
- `src/infrastructure/daemon/lsp_handler.py:73-101`
- `src/infrastructure/lsp_client.py:359-389`
- `src/infrastructure/lsp_client.py:502-532`

**Evidence**
Debug markers found in code:
- `[LSP_HANDLER] >> request ENTER ...`
- `[LSP_HANDLER] << request RETURN ...`
- `[LSP_HANDLER] !! request EXCEPTION ...`
- `[LSP_LOOP_MSG] ...`
- `[LSP_LOOP_SET] ...`
- `[LSP_LOOP_ERROR] ...`
- `[LSP_LOOP_ORPHAN] ...`
- `[LSP_REQ_SENT] ...`
- `[LSP_REQ_WAIT] ...`
- `[LSP_REQ_RESULT] ...`
- `[LSP_REQ_TIMEOUT] ...`

**Problem**
These diagnostics are always active and write to `stderr` in production code paths.
Because the daemon redirects stderr/stdout to its runtime log, they become persistent operational logs rather than temporary local debug output.

**Consequences**
- noisy runtime logs
- harder operator signal-to-noise ratio
- possible leakage of internal method names, ids, and error details into logs
- brittle observability if people start depending on debug strings as signals

**Do we have logs to identify it?**
- **Yes**
- This is the one problem that logs directly expose.
- The log sink is the daemon runtime log via `DaemonManager.start()`.
- If the daemon is started through the official path, these markers should appear in the daemon log.

**Do we have tests to prove it?**
- **No explicit tests**
- Existing tests validate behavior, not absence/presence of debug logs.
- No guard exists to ensure logs are gated behind a debug flag.

**Recommended next test**
- Add a unit test that verifies no debug log is emitted by default, or gate these logs behind `TRIFECTA_LSP_DEBUG=1` and test both enabled/disabled modes.

---

### 3. Observable semantic change for `FAILED` state

**Severity:** Major  
**File:** `src/infrastructure/daemon/lsp_handler.py`  
**Lines:** `31-36` and ordering relative to `38-42`  

**Evidence**
- `src/infrastructure/daemon/lsp_handler.py:31-36` now handles `LSPState.FAILED` before `is_ready()`
- `tests/unit/daemon/test_lsp_handler.py:45-49` now expects `fallback_reason == "lsp_error"`

**Problem**
The observable response semantics changed:
- before, `FAILED` effectively followed the broader “not ready” path,
- now `FAILED` is mapped explicitly to `lsp_error`.

This may be reasonable, but it is a **contract change**, not just an internal refactor.

**Consequences**
- clients or operators may see different fallback reasons
- dashboards or parsers that distinguish `lsp_not_ready` vs `lsp_error` can shift behavior
- mixes behavior change into a drift set that was previously bounded more narrowly

**Do we have logs to identify it?**
- **Not directly**
- Debug logs may show request lifecycle, but they do not provide a clear semantic audit trail specifically for this fallback-reason change.
- This issue is better identified by response assertions than by logs.

**Do we have tests to prove it?**
- **Yes**
- `tests/unit/daemon/test_lsp_handler.py:45-49` explicitly proves the new behavior:
  - `FAILED -> lsp_error`

**Coverage gap**
- No migration/contract note ties this semantic change to a documented external decision.

---

### 4. Timeout configuration is introduced without full contract coverage

**Severity:** Major  
**Files:**
- `src/platform/daemon_manager.py`
- `src/infrastructure/lsp_client.py`

**Lines**
- `src/platform/daemon_manager.py:41`
- `src/platform/daemon_manager.py:76-80`
- `src/infrastructure/lsp_client.py:478-486`
- `src/infrastructure/lsp_client.py:502-532`

**Evidence**
- `src/platform/daemon_manager.py:41`
  - class attribute reads `TRIFECTA_LSP_REQUEST_TIMEOUT` at import time
- `src/platform/daemon_manager.py:80`
  - env is propagated to daemon process
- `src/infrastructure/lsp_client.py:478-486`
  - `request()` reads `TRIFECTA_LSP_REQUEST_TIMEOUT` when `timeout is None`

**Problem**
The timeout is now configurable in two coupled layers, but the behavior is not fully tested/documented.
Also, `DaemonManager.LSP_REQUEST_TIMEOUT` is computed at class load time, which can surprise callers/tests that mutate env later.

**Consequences**
- timeout behavior may vary depending on import timing
- harder reproducibility in tests and CLI sessions
- possible mismatch between expected daemon request timeout and actual runtime timeout

**Do we have logs to identify it?**
- **Partially**
- Debug logs in `LSPClient.request()` include timeout values:
  - `src/infrastructure/lsp_client.py:502`
  - `src/infrastructure/lsp_client.py:506`
  - `src/infrastructure/lsp_client.py:532`
- But we do **not** have a dedicated contract log proving correct propagation from `DaemonManager` to `LSPClient` in the official daemon process.

**Do we have tests to prove it?**
- **Not enough**
- Present tests cover ready semantics and repo_root behavior, but not timeout propagation or invalid env parsing end-to-end.
- No focused test was found for:
  - `DaemonManager` exporting timeout correctly
  - `LSPClient.request()` honoring default timeout via env
  - invalid env values falling back predictably

**Recommended next tests**
- unit test for `DaemonManager.start()` env composition including `TRIFECTA_LSP_REQUEST_TIMEOUT`
- unit test for `LSPClient.request(timeout=None)` with env values:
  - valid numeric value
  - invalid value
  - unset value
- integration test proving the official daemon path uses the configured timeout

---

## Current test map

### Tests that already support the drift analysis
- `tests/unit/daemon/test_lsp_handler.py`
  - covers unavailable / not ready / failed / success / empty / exception paths
- `tests/unit/daemon/test_lsp_handler_didopen_format.py`
  - covers didOpen transformation and language detection
- `tests/unit/test_lsp_ready_contract.py`
  - covers relaxed READY contract after initialize handshake
- `tests/integration/test_ready_semantics_documented_and_enforced.py`
  - covers READY and invariant failure semantics

### Important missing tests
1. Notification send failure / no-op does not falsely report success
2. Debug logging is gated or absent by default
3. Timeout env propagation from `DaemonManager` to daemon child process
4. `LSPClient.request()` env timeout parsing contract

---

## Logs status summary

| Issue | Do logs help identify it? | Notes |
|---|---|---|
| Silent success in notifications | Partial / weak | no authoritative success signal after `_send_rpc()` |
| Production debug logs left enabled | Yes | debug markers will appear in daemon runtime log |
| FAILED semantic change | Weak | better identified by tests than logs |
| Timeout config propagation | Partial | request logs show timeout values, but not full propagation contract |

---

## Final verdict

**Request Changes**

The current drift contains useful ideas, but it is not clean enough to absorb blindly into the previously validated daemon batch.

Minimum remediation before merge:
1. Remove or gate debug logs
2. Decide the notification success contract and test it explicitly
3. Decide whether `FAILED -> lsp_error` is a deliberate external contract change
4. Add timeout propagation tests before keeping the new env-based timeout path
