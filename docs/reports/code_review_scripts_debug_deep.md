# Code Review: scripts/debug/debug_client.py

**Reviewer:** Antigravity (Simulated Code Review Agent)
**Date:** 2026-01-06
**Target:** `scripts/debug/debug_client.py`

## Strengths
- **Simple Purpose**: Clearly demonstrates how to instantiate `LSPClient` manually.
- **Logging**: Configures debug logging upfront which is useful for debugging.

## Issues

### Critical (Must Fix)

1.  **Race Condition / Busy Wait**
    - **File:** `scripts/debug/debug_client.py:46-51`
    - **Issue:** The `for _ in range(10)` loop executes without any delay. It will complete almost instantly. Since `client.start()` is asynchronous (threaded/subprocess), the client effectively never has time to become `READY` before the loop exits.
    - **Fix:** Add `import time` and `time.sleep(1)` inside the loop.

2.  **Resource Leak Risk**
    - **File:** `scripts/debug/debug_client.py:34-53`
    - **Issue:** `client.stop()` is called at the end. If an exception occurs (e.g., file not found, crash in loop), `client.stop()` is never reached, potentially leaving orphan LSP processes or open ports.
    - **Fix:** Wrap execution in a `try...finally` block.

### Important (Should Fix)

1.  **Fragile Path Logic**
    - **File:** `scripts/debug/debug_client.py:9-13`
    - **Issue:** `sys.path.insert` hack relies on file location relative to root. breaks if script is moved or symlinked.
    - **Fix:** Run as a module `uv run python -m scripts.debug.debug_client` and remove path hacks.

2.  **Hardcoded Test Target**
    - **File:** `scripts/debug/debug_client.py:41`
    - **Issue:** Hardcoded path to `src/infrastructure/cli.py`. If this file is refactored/moved, the debug script breaks silently (or noisy error).
    - **Fix:** Use `__file__` (self) or accept argument via `sys.argv`.

### Minor (Nice to Have)

1.  **Telemetry Suppression**
    - **File:** `scripts/debug/debug_client.py:37`
    - **Issue:** Passing `telemetry=None`. While fine for debug, it differs from prod.
    - **Fix:** Consider passing a `MockTelemetry` or allowing telemetry to see debug events.

## Assessment

**Ready to merge? No.**

**Reasoning:** The **Busy Wait** bug renders the script functionally broken for its intended purpose (waiting for startup), as it exits too fast. The lack of `try/finally` creates cleanup risks.
