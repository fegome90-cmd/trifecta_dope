# Code Review Report: scripts/debug (Deep Analysis)

**Reviewer:** Antigravity (Simulated Code Review Agent)
**Date:** 2026-01-06
**Scope:** `scripts/debug` (All files)

## Executive Summary
The folder contains loose utility scripts. While useful for ad-hoc debugging, they lack robustness, error handling, and environmental stability. **Rule 1 Violation**: These should be formalized into CLI commands or standard test harnesses.

---

## File: `debug_client.py`

### Critical (Must Fix)
1.  **Race Condition / Busy Wait** (Line 46): The `range(10)` loop spins instantly. It **will fail** to detect a valid startup sequence unless the machine is infinitely fast.
    *   *Fix*: Add `time.sleep(0.5)`.
2.  **Resource Leak** (Line 34): No `try/finally` for `client.stop()`. Crash = Zombie Process.

### Important
1.  **Hardcoded Path**: `root / "src/infrastructure/cli.py"` makes the script fragile to refactoring.

---

## File: `debug_status.py`

### Critical (Must Fix)
1.  **Unnamed Exception Handling**: `client.send()` involves socket IO. If the daemon is not running, this line likely raises `ConnectionRefused` or `FileNotFoundError` (socket). Code has no `try/catch`, so it crashes instead of reporting "Daemon DOWN".
    *   *Fix*: Wrap in `try: ... except Exception: print("Daemon not running")`.

### Important
1.  **Context Ambiguity**: `resolve_segment_root()` depends entirely on CWD. Running this script from `/tmp` vs `project_root` yields different behavior without user feedback.
    *   *Fix*: Print `root` immediately (it does, good) but allow passing root via arg.

---

## File: `debug_ts.py`

### Important
1.  **API Fragility**: Tree-sitter bindings change frequently. This script uses `Language(ptr)` and `Parser(lang)`.
    *   *Risk*: If `tree-sitter` pypi package is upgraded, this script validates *nothing* relevant to the actual `src` code if the `src` uses a different abstraction or wrapper.
    *   *Recommendation*: Import the parser factory used in `src/infrastructure/ast` instead of rewriting raw instantiation logic.

---

## Global Issues (All Files)

1.  **Sys.Path Hacks (Rule 1)**
    *   `debug_client.py` and `debug_status.py` manipulate `sys.path`. This guarantees that `import src...` works differently here than in production CLI.
    *   *Fix*: Run as modules (`python -m scripts.debug.client`) or formalize into `src/cli/debug.py`.

## Assessment

**Verdict: 🔴 NOT PRODUCTION READY**

**Recommendation:**
1.  Fix the Busy Wait in `debug_client.py` immediately (blocker for use).
2.  Wrap connection logic in `debug_status.py` to handle "Daemon Down" gracefully.
3.  Migrate all scripts to a proper entry point or move to `eval/manual/`.
