## T4 — Budget/backpressure behavior
**Objetivo**: Controlar el consumo de tokens.

- **Archivos tocados**:
  - `src/application/context_service.py`
  - `src/application/use_cases.py`
- **Cambios concretos**:
  - **Antes**: Sin ordenamiento por valor.
  - **Después**: Ordenamiento por Value-per-Token. Truncado inteligente.
- **Comandos ejecutables**:
  - `trifecta ctx get --segment . --ids ID --budget-token-est 400`
- **DoD / criterios de aceptación**:
  - Output incluye nota de advertencia si hubo backpressure.
- **Riesgos mitigados**:
  - **Explosión de tokens**: Controlada.

---
