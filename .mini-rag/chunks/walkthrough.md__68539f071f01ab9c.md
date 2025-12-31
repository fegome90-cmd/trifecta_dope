## Failure Modes (Strict Gates)

| Escenario | Comportamiento del Sistema | Acción Requerida |
| :--- | :--- | :--- |
| **Search sin hits** | Retorna vacío. **NO hace fallback automático** a fullfiles en Plan A. | Usuario debe refinar query o invocar explícitamente `--mode fullfiles`. |
| **Budget Exceeded** | `ctx get` retorna `excerpt` + highlight warning. | Solicitar chunks específicos o aumentar `--budget-token-est`. |
| **Pack Stale/Invalid** | `ctx validate` falla (exit 1). `load` en modo PCC **falla fast** (Fail-Closed). | Ejecutar `trifecta ctx sync` (o build) para regenerar. **NO** usar contextos corruptos. |
| **Pack Missing** | `load` (default) detecta ausencia y cae a Plan B. | Alerta "Pack not found, using heuristics". **Nota**: `ctx search/get` NO hacen fallback; fallan si no hay pack. |
