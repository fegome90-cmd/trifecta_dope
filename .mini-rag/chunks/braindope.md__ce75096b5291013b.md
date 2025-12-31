# 8) Fail Fast Contract Validation

El agente debe validar el contrato antes de responder:

1. **Leer** `profile` del frontmatter.
2. **Verificar** que su output cumple `output_contract`.
3. **Si falla**: Responder `ContractCheck: FAIL` y proponer perfil correcto.

---
