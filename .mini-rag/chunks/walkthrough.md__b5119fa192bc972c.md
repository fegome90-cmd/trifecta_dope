#### Contrato YAML (session.md)
> ⚠️ **Este contrato NO es ejecutado por el sistema en v1.** Es puramente documental o para futuras versiones.

````md
## TRIFECTA_SESSION_CONTRACT
```yaml
schema_version: 1
segment: .
autopilot:
  enabled: true
  debounce_ms: 800
  lock_file: _ctx/.autopilot.lock
  allow_prefixes: ["trifecta ctx "]
  steps:
    - name: build
      cmd: "trifecta ctx build --segment ."
      timeout_sec: 60
    - name: validate
      cmd: "trifecta ctx validate --segment ."
      timeout_sec: 30
```
````

- **DoD / criterios de aceptación**:
  - El YAML existe como referencia pero está marcado explícitamente como NO ejecutable.
  - El sistema funciona sin leer `session.md`.
- **Riesgos mitigados**:
  - **Complejidad innecesaria**: Se evita parsers y lógica de orquestación en v1.

---
