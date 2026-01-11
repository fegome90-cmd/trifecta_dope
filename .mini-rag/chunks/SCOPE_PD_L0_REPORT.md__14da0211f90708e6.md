### 1. ¿Dónde se decide “leer poco vs leer más”?
La lógica reside en `src/application/context_service.py:86` (`ContextService.get`). Se basa en el parámetro `mode` (`raw`, `excerpt`, `skeleton`) y el `budget_token_est`.
