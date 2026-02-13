# Handoff: WO-0040 - Explicit Fallback Contract

## Summary
Implemented explicit fallback contract for LSP responses to eliminate silent fallbacks.

## Changes Made
- Created `src/domain/lsp_contracts.py` with LSPResponse dataclass
- Modified `src/infrastructure/cli_ast.py` hover command
- Added 9 integration tests in `tests/integration/test_lsp_contract_fallback.py`

## Contract Fields
Every LSP response now includes:
- `capability_state`: FULL, DEGRADED, WIP, UNAVAILABLE
- `fallback_reason`: enum of reasons (lsp_not_ready, lsp_not_implemented, etc.)
- `backend`: lsp_pyright, lsp_pylsp, ast_only, wip_stub, unavailable
- `response_state`: complete, partial, error, degraded

## Testing
All 9 tests passing:
- 5 unit tests for LSPResponse contract
- 3 integration tests for hover command
- 1 telemetry event test

## Commands Used
```bash
uv run pytest tests/integration/test_lsp_contract_fallback.py -v
uv run trifecta ast hover <file> --line 1 --char 1 --segment .
```

## Commit SHA
06ea690
