### [P2] 9. Hardcoded `_ctx/` Path Literals

- **Señal (command)**: `rg '_ctx/' src`
- **Ubicación**: 30+ locations across `cli.py`, `validators.py`, `templates.py`, `use_cases.py`
- **Riesgo**: Context directory hardcoded as `_ctx/`. Renaming requires a mass find-replace.
- **Fix lean** (<= 60 líneas):
  Define `CTX_DIR = "_ctx"` constant in `src/domain/constants.py`. Replace all string literals.
- **Tripwire test**: `test_no_hardcoded_ctx_literals`
  ```python
  def test_no_hardcoded_ctx_literals():
      for f in Path("src").rglob("*.py"):
          if "constants.py" in str(f):
              continue
          assert '"_ctx/' not in f.read_text(), f"Use CTX_DIR constant in {f}"
  ```
- **Evidencia requerida**: `rg '"_ctx/' src --count`

---
