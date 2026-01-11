# Fix Debug Scripts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Formalize `scripts/debug` contents into audit-grade, robust CLI commands or harnesses, resolving race conditions and path hacks.

**Architecture:** Move logic from loose scripts to `src/application/use_cases/debug_lsp.py` and expose via `src/interfaces/cli/debug.py` (Command: `trifecta debug`). This strictly satisfies **Rule 1 (Use the CLI)** and removes all loose scripts.

**Tech Stack:** Python, Trifecta LSPClient, Pytest (for verification logic).

---

### Task 1: Create 'trifecta debug' CLI Command

**Files:**
- Create: `src/application/use_cases/debug_lsp.py` (Business Logic)
- Modify: `src/infrastructure/cli.py` (Register `debug` group)
- Delete: `scripts/debug/`

**Step 1: Write the failing test (TDD)**

Test that `trifecta debug client` command exists and fails gracefully when daemon is down.

**Step 2: Implement Use Cases (Green)**
1.  `LspClientDebugUseCase`: Handles client lifecycle with `try/finally` and proper `sleep`.
2.  `LspStatusDebugUseCase`: Handles socket checking without crashing.

**Step 3: Register in CLI**
Expose `trifecta debug client` and `trifecta debug status`.

**Step 4: Verification**
Run `uv run trifecta debug status` -> "Daemon not found" (Clean exit).

---


---

### Task 3: Cleanup Loose Scripts

**Files:**
- Delete: `scripts/debug/` (Recursively)

**Step 1: Verify replacements work**
Rerun both harnesses.

**Step 2: Delete old scripts**
`rm -rf scripts/debug`

**Step 3: Commit**
`git commit -m "refactor(debug): replace loose scripts with robust harnesses (Rule 6 fix)"`
