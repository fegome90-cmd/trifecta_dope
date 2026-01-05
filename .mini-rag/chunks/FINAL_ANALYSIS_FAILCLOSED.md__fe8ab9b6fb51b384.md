## 4) QUÉ SE "OCULTA" EN OUTPUTS (CLEAN)

**Campos filtrados en `session query --format clean`** (NO es borrado, es limpieza de output):

| Campo | Por qué se oculta | Riesgo de Contrato | Cómo acceder RAW |
|:------|:------------------|:-------------------|:-----------------|
| `run_id` | Irrelevante para session context | BAJO - comando nuevo sin dependencias | `--format raw` |
| `segment_id` | Ya conocido por CLI | BAJO | `--format raw` |
| `timing_ms` | Siempre 0 para session (no tiene latencia) | BAJO | `--format raw` |
| `warnings` | Siempre vacío para session | BAJO | `--format raw` |

**Evidencia** (FINAL_PROPOSAL:L29-L33):
> **Campos ELIMINADOS del output**:  
> - `run_id` (irrelevante para session context)  
> - `segment_id` (ya conocido por CLI)  
> - `timing_ms` (siempre 0 para session)  
> - `warnings` (siempre vacío para session)

**Reducción estimada**: ~40% menos tokens por entry (FINAL_PROPOSAL:L48)

**IMPORTANTE**: Estos campos **siguen existiendo** en `_ctx/telemetry/events.jsonl`. Solo se ocultan en output limpio.

**Acceso completo**:
```bash
# Output limpio (sin campos telemetry)
trifecta session query -s . --last 5 --format clean

# Output raw (todos los campos)
trifecta session query -s . --last 5 --format raw
```
