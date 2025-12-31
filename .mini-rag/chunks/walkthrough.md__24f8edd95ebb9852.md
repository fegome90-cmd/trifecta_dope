## T2 — Atomic write + lock
**Objetivo**: Asegurar que la creación del pack de contexto sea atómica y segura ante concurrencia.

- **Archivos tocados**:
  - `src/application/use_cases.py` (`BuildContextPackUseCase`, `ValidateContextPackUseCase`)
- **Cambios concretos**:
  - **Antes**: Escritura directa.
  - **Después**: `AtomicWriter` (tmp->fsync->rename) y lock `_ctx/.autopilot.lock`. Validator profundo.
- **Comandos ejecutables**:
  - `trifecta ctx build --segment .`
  - `trifecta ctx validate --segment .`
- **DoD / criterios de aceptación**:
  - `ctx validate` falla si se cambia un solo carácter de un archivo fuente.
  - Bloqueo concurrente verificado.
- **Riesgos mitigados**:
  - **Corrupción**: Evitada vía escrituras atómicas.

---
