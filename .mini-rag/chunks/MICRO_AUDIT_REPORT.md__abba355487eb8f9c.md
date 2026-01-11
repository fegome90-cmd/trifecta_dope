### [P1] 3. Excessive `pytest.skip()` in Acceptance Tests

- **Señal (command)**: `rg 'pytest\.skip' tests`
- **Ubicación**: `tests/acceptance/test_pd_evidence_stop_e2e.py:48,58,71,80,176,187,271,368,379`
- **Riesgo**: 9 conditional skips in one acceptance test file. Tests can pass in CI without actually exercising the happy path. "Verde falso."
- **Fix lean** (<= 60 líneas):
  1. Create a `@pytest.fixture` that sets up a known-good segment with `trifecta create`.
  2. Replace conditional skips with `pytest.fail()` when preconditions not met.
  3. Mark truly environment-dependent tests with `@pytest.mark.slow`.
- **Tripwire test**: `test_no_skip_in_acceptance_tests`
  ```python
  def test_no_skip_in_acceptance_tests():
      import ast
      for f in Path("tests/acceptance").glob("*.py"):
          tree = ast.parse(f.read_text())
          skips = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and getattr(n.func, "attr", "") == "skip"]
          assert len(skips) == 0, f"Remove pytest.skip from {f}"
  ```
- **Evidencia requerida**: `pytest tests/acceptance/ -v --tb=short`

---
