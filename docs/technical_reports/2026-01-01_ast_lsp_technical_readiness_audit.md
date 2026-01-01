# Technical Readiness Audit: AST/LSP Implementation (v0.2 - DEEP DIVE)

**Date**: 2026-01-01
**Status**: **CRITICAL GAPS IDENTIFIED**
**Reference Plan**: `docs/plans/ast_lsp.md`

## 1. Executive Summary: "Ghost Implementation"

The codebase contains the *logic* for AST and LSP, but it is **completely disconnected** from the application. The features requested (and planned) are **not accessible** to the agent or user.

- **CLI (`cli.py`)**: MISSING `trifecta ast` commands.
- **Search (`SearchUseCase`)**: MISSING integration with `SymbolSelector`. It still does naive text search.
- **LSP (`LSPManager`)**: ORPHANED. No code instantiates or starts the LSP manager.

**Verdict**: The PR delivered the *engine* but not the *steering wheel*. The feature is effectively **0% usable**.

---

## 2. Detailed Gap Analysis

### 2.1 CLI Integration (Critical)
*   **Plan (T3)**: `ast symbols`, `ast locate`, `ast snippet`.
*   **Actual**: `src/infrastructure/cli.py` has ZERO references to `ast_parser` or `lsp_manager`.
*   **Impact**: Agent cannot execute the "Step 2" of the plan (AST navigation).

### 2.2 Integration Wiring (Critical)
*   **Plan (T7)**: Progressive Disclosure (Map -> Snippet -> File).
*   **Actual**: `src/application/use_cases.py` and `search_get_usecases.py` are purely legacy logic. `ContextService` does not know about AST skeletons.
*   **Impact**: The "Progressive Disclosure" feature is non-existent.

### 2.3 Code Quality & Safety (High)
*   **AST Parser**: `_extract_symbols` is recursive without depth limit. Vulnerable to `RecursionError` on deep code.
*   **LSP Manager**: `stderr=subprocess.DEVNULL` blindly suppresses all startup errors. If `pyright` is missing or crashes, the system fails silently.
*   **Symbol Selector**: Logic is fragile (exact match only). If code drifts by 1 character (e.g., refactor), the selector breaks.

---

## 3. Required Remediation Plan (Immediate)

We must treat this as a "Feature Incomplete" state, not just "Buggy".

### 3.1 Step 1: expose the tools (CLI)
Create `src/infrastructure/cli_ast.py` and wire it into `cli.py`:
- `trifecta ast symbols <query>` -> calls `SymbolSelector`
- `trifecta ast locate <sym_uri>` -> calls `ASTParser`
- `trifecta ast verify` -> runs the 3 safety tests

### 3.2 Step 2: Wire Safety Nets (Tests)
Create `tests/integration/test_ast_integration.py`:
- **Test**: Instantiate `LSPManager`, force it to START, verify PID exists.
- **Test**: Parse a `fixture.py` with `ASTParser`, verify specific symbols returned.
- **Fault Injection**: Rename `fixture.py` while LSP is running. Verify system doesn't crash.

### 3.3 Step 3: Progressive Logic
Update `ContextService` to:
1. Check if query looks like a symbol (`AuthManager`).
2. If yes, query `ASTParser` first.
3. If hit, return `skeleton` or `snippet` instead of full file.

---

## 4. Root Cause Analysis
The PR likely focused on "getting the classes written" (T1, T4, T5) but skipped the "application layer" (T3, T7) entirely. The tests passed because they tested the *classes in isolation*, not the *app*.

## 5. Recommendation
**STOP** verification. **START** Implementation Phase 2 (Integration).
Do not try to verify features that don't exist in the CLI. The priority is to wire them up.
