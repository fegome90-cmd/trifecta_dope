### Phase 2: Agent Skill (1 hora)

| Task | Archivo | Descripción |
|------|---------|-------------|
| 2.1 | `telemetry_analysis/skills/analyze/skill.md` | Skill definition |
| 2.2 | `telemetry_analysis/skills/analyze/examples/` | Output examples |

**Skill Structure**:
```markdown
# telemetry-analyze

Genera reporte conciso de telemetry del CLI Trifecta.

## Output Format

SIEMPRE usar este formato exacto:

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------:|
| Commands totales | 49 |
| Búsquedas | 19 |
| Hit rate | 31.6% |
| Latencia promedio | 0.5ms |

## Top Commands

| Comando | Count | % |
|---------|------:|---|
| ctx.search | 19 | 38.8% |
| ctx.sync | 18 | 36.7% |

NO escribir más de 50 líneas. SIEMPRE usar tablas.
```
