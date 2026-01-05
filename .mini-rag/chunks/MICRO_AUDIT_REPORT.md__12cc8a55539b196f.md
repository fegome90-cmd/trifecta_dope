### [P1] 6. Missing Precedence Documentation for TRIFECTA_* Env Vars

- **Señal (command)**: `rg 'TRIFECTA_' src`
- **Ubicación**: `src/infrastructure/cli.py:69,343,354`, `src/infrastructure/deprecations.py:33`
- **Riesgo**: 4 env vars exist but no single source of truth documents the default → env → flag precedence. Agents and users may set conflicting values.
- **Fix lean** (<= 60 líneas):
  Create `docs/ENV_VARS.md` with precedence table (see below). Add docstring to CLI functions referencing it.
- **Tripwire test**: `test_env_var_precedence_documented`
  ```python
  def test_env_var_precedence_documented():
      doc = Path("docs/ENV_VARS.md").read_text()
      for var in ["TRIFECTA_TELEMETRY_LEVEL", "TRIFECTA_PD_MAX_CHUNKS",
                  "TRIFECTA_PD_STOP_ON_EVIDENCE", "TRIFECTA_DEPRECATED"]:
          assert var in doc
  ```
- **Evidencia requerida**: `cat docs/ENV_VARS.md`

---
