### [P1] 4. CWD Coupling in Integration Tests

- **Señal (command)**: `rg 'Path\.cwd\(\)' tests`
- **Ubicación**: `tests/integration/test_lsp_daemon.py:23`, `tests/integration/test_lsp_telemetry.py:12,60,71,104,118`
- **Riesgo**: Tests use `Path.cwd()` instead of `tmp_path` fixture. Running tests from different directory or in parallel can cause cross-contamination.
- **Fix lean** (<= 60 líneas):
  ```python
  # Before:
  root = Path.cwd()
  # After:
  root = tmp_path
  ```
  Update 6 test files to accept `tmp_path` fixture and create isolated segments.
- **Tripwire test**: `test_no_cwd_in_tests`
  ```python
  def test_no_cwd_in_tests():
      for f in Path("tests").rglob("*.py"):
          content = f.read_text()
          assert "Path.cwd()" not in content or "tmp_path" in content
  ```
- **Evidencia requerida**: `rg 'Path\.cwd' tests --count`

---
