### Test Suite

```bash
$ uv run pytest tests/ -v
============================= 144 passed in 0.28s ==============================
```

**Coverage Breakdown**:

1. **Code Discipline**: `test_codebase_discipline.py` (Prohibits `.unwrap()` in src).
2. **FP Gate**: 17 tests (Result Monad, FP Validators, CLI Gate).
3. **Strict Contract**: 7 tests (Symmetric/Determinism).
    - `test_build_fails_with_multiple_session_files` (Multiple Sessions: FAIL)
    - `TODO: add test_missing_session_fails` (Missing Session: FAIL)
    - `test_build_fails_with_contaminated_agent_suffix` (Contamination: FAIL)
    - `test_build_fails_with_multiple_agent_files` (Ambiguity: FAIL)
4. **Legacy Failure**: 3 tests (Integration scenarios).
