## C) ¿Hay early-stop real?

- **En el código**: **NO EXISTE** una condición de stop basada en "evidencia encontrada". El stop es puramente por *presupuesto de tokens* (Backpressure).
- **En la CLI**: Existe el límite `budget_token_est`. No hay límites de `max_chunks` o `max_chars` explícitos fuera de la estimación de tokens.
- **En telemetría**: **NO EXISTE** el campo `stop_reason`. Solo se infiere el stop si `trimmed: true` en el evento `ctx.get`.

---
