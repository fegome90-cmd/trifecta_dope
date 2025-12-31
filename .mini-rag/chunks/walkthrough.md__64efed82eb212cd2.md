## T3 — CLI ctx sync (Macro Fija)
**Objetivo**: Proveer un comando unificado para regenerar el contexto sin lógica compleja.

- **Archivos tocados**:
  - `src/infrastructure/cli.py`
- **Cambios concretos**:
  - **Antes**: Lógica dispersa o inexistente.
  - **Después**: `trifecta ctx sync` ejecuta una macro fija: `ctx build` → `ctx validate`.
  - **Importante**: No parsea `session.md` y no depende de `TRIFECTA_SESSION_CONTRACT`.

- **Comandos ejecutables**:
  ```bash
  trifecta ctx sync --segment .
  # Equivalente a:
  # trifecta ctx build --segment . && trifecta ctx validate --segment .
  ```
- **DoD / criterios de aceptación**:
  - `ctx sync` regenera y valida el pack en un solo paso.
- **Riesgos mitigados**:
  - **Desincronización**: Un solo comando garantiza que el pack esté fresco y válido.

---
