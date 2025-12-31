# Trifecta CLI Telemetry - Data Science Plan

> **Plan Vivo**: Actualizado continuamente conforme se investiga e implementa
> **Fecha inicio**: 2025-12-31
> **Objetivo**: Sistema simple de análisis de telemetry para que agentes reporten uso del CLI

---

## Investigación Completada (Web Search 2025-12-31)

### Best Practices de CLI Telemetry

**Fuente**: [6 telemetry best practices for CLI tools - Massimiliano Marcon](https://marcon.me/articles/cli-telemetry-best-practices/)

1. **Be intencional** - Tracking plan defining exactamente qué capturar
2. **Transparencia** - Mostrar cómo deshabilitar telemetry
3. **Múltiples formas de opt-out** - Commands, env vars, config files
4. **Performance first** - Best-effort sending con timeouts
5. **Environment data** - OS, Docker usage para platform decisions
6. **High volume prep** - Scripting y CI generan muchos eventos

### Tools para CLI Reporting

| Herramienta | Uso | Link |
|-------------|-----|------|
| **sqlite-utils** | CLI para manipular SQLite | [docs](https://sqlite-utils.datasette.io/en/stable/cli.html) |
| **tabulate** | Tablas ASCII en terminal | [PyPI](https://pypi.org/project/tabulate/) |
| **Rich** | Formato rico + tablas en terminal | [GitHub](https://github.com/Textualize/rich) |
| **terminaltables** | ASCII art tables | [PyPI](https://pypi.org/project/terminaltables/) |
| **Click** | Framework CLI (ya usado) | [docs](https://click.palletsprojects.com/) |

### Log Analysis Workflow

**Fuente**: [Log Analysis Using SQLite - Drew Csillag](https://drewcsillag.medium.com/log-analysis-using-sqlite-1cfdd40aa6f9)

1. Parse JSON log files con Python
2. Insert en SQLite (transactions para performance)
3. SQL queries para análisis
4. Generar reportes desde SQLite

### Agentes - Structured Output

**Fuentes**:
- [Skill Authoring Best Practices (Claude)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Report Generator Skill](https://claude-plugins.dev/skills/@PsAccelerator/Claude/Reports)

**Principios clave**:
- **JSON Schema enforcement** para output predecible
- **Examples > Explanations** - Un ejemplo comunica más que párrafos
- **Smart Brevity** - Output conciso, estructurado
- **Output templates** con placeholders

---

## Estado Actual

### Existe
- ✅ `src/infrastructure/telemetry.py` - Clase Telemetry (JSONL con rotación)
- ✅ `_ctx/telemetry/events.jsonl` - 49 eventos registrados
- ✅ `telemetry_analysis/scripts/analyze.py` - Script básico de análisis
- ✅ `docs/data/2025-12-30_telemetry_analysis.md` - Análisis previo

### Problemas Identificados
- ❌ **Sin skill para agentes** - Cada agente genera "textos bíblicos" diferentes
- ❌ **Sin reporte CLI** - No hay comando simple para ver stats
- ❌ **Sin visualización terminal** - No hay tablas/charts en CLI
- ❌ **Workflow manual** - Requiere ejecutar scripts manualmente

---

## Diseño Propuesto

### Arquitectura Simple

```
┌─────────────────────────────────────────────────────────────┐
│                    Trifecta CLI (User/Agent)                 │
│                                                              │
│  ctx.search → Telemetry.event() → events.jsonl (append)    │
│  ctx.get    → Telemetry.event() → metrics.json (aggregate) │
│  ctx.sync   → Telemetry.event() → last_run.json (summary)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    New: CLI Report Command                   │
│                                                              │
│  $ trifecta telemetry report [--last N] [--format table]    │
│  $ trifecta telemetry export [--format json|csv]            │
│  $ trifecta telemetry chart [--type hits|latency]           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   New: Agent Skill (telemetry-analyze)       │
│                                                              │
│  Usa la skill → Output conciso en Markdown                   │
│  - Tablas ASCII                                              │
│  - Métricas clave solo                                       │
│  - Sin "textos bíblicos"                                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Capture (ya existe)**
   - Cada comando CLI → `Telemetry.event(cmd, args, result, timing)`
   - JSONL append-only con rotación

2. **Analysis Scripts (nuevos)**
   ```bash
   # Reporte rápido en terminal
   trifecta telemetry report

   # Exportar para análisis externo
   trifecta telemetry export --format json > data.json

   # Charts ASCII en terminal
   trifecta telemetry chart --type hits --days 7
   ```

3. **Agent Skill (nuevo)**
   - Skill: `telemetry-analyze`
   - Input: archivo de telemetry
   - Output: Markdown conciso con tablas

---

## Plan de Implementación

### Phase 1: CLI Commands (2-3 horas)

| Task | Archivo | Descripción |
|------|---------|-------------|
| 1.1 | `src/infrastructure/cli.py` | Add `telemetry` command group |
| 1.2 | `src/application/telemetry_reports.py` | Report generation logic |
| 1.3 | `src/application/telemetry_charts.py` | ASCII charts con `asciichart` |

**Commands**:
```bash
# Reporte resumido
trifecta telemetry report [--last 7d]

# Exportar datos
trifecta telemetry export [--format json|csv]

# Chart en terminal
trifecta telemetry chart --type hits|latency|errors [--days 7]
```

**Libraries a agregar**:
- `tabulate` - Tablas ASCII
- `asciichart` - Gráficos ASCII
- `rich` - Formato rico (opcional)

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

### Phase 3: SQLite Analytics (opcional, 1-2 horas)

| Task | Archivo | Descripción |
|------|---------|-------------|
| 3.1 | `scripts/etl_telemetry.py` | JSONL → SQLite ETL |
| 3.2 | `src/infrastructure/telemetry_db.py` | SQLite schema y queries |

**SQLite Schema**:
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    command TEXT NOT NULL,
    args_json TEXT,
    result_json TEXT,
    timing_ms INTEGER
);

CREATE INDEX idx_command ON events(command);
CREATE INDEX idx_timestamp ON events(timestamp);
```

---

## Output Examples

### CLI Report

```
$ trifecta telemetry report --last 7d

╭─────────────────────────────────────────────────╮
│         Trifecta Telemetry Report                │
│              Last 7 days                         │
╰─────────────────────────────────────────────────╯

Summary
───────────────────────────────────────────────────
  Total commands:      49
  Unique sessions:     3
  Avg latency:         1.2ms

Top Commands
───────────────────────────────────────────────────
  ctx.search           19  (38.8%)
  ctx.sync             18  (36.7%)
  ctx.get               6  (12.2%)
  load                  4  ( 8.2%)
  ctx.build             2  ( 4.1%)

Search Effectiveness
───────────────────────────────────────────────────
  Total searches:      19
  With hits:            6  (31.6%)
  Zero hits:           13  (68.4%)  ⚠️

Recent Queries (Failed)
───────────────────────────────────────────────────
  "telemetry class"            → 0 hits
  "validators deduplication"    → 0 hits
  "sequential thinking"         → 0 hits
```

### ASCII Chart

```
$ trifecta telemetry chart --type hits --days 7

Daily Search Hits (Last 7 Days)
────────────────────────────────────────

    10 ┤
     9 ┤
     8 ┤        ┌───┐
     7 ┤        │   │       ┌───┐
     6 ┤    ┌───┤   ├───┐   │   │
     5 ┤    │   │   │   │   │   │
     4 ┤────┤   │   │   │   │   ├───
     3 ┤    │   │   │   │   │   │
     2 ┤    │   │   │   │   │   │
     1 ┤    │   │   │   │   │   │
     0 ┼────┴───┴───┴───┴───┴───┴───→
       Mon  Tue  Wed  Thu  Fri  Sat  Sun
```

### Agent Skill Output

```markdown
## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------:|
| Commands totales | 49 |
| Búsquedas | 19 |
| Hit rate | 31.6% |
| Latencia promedio | 1.2ms |

## Top Commands

| Comando | Count | % |
|---------|------:|---:|
| ctx.search | 19 | 38.8% |
| ctx.sync | 18 | 36.7% |
| ctx.get | 6 | 12.2% |

## Insights

- ⚠️ **68.4% de búsquedas sin resultados** - Considerar expandir index
- ✅ **Latencia excelente** - Todas las operaciones < 5ms
- ✅ **Uso estable** - ~7 commands/day promedio
```

---

## Sources Referenciados

### CLI Telemetry
- [6 telemetry best practices for CLI tools](https://marcon.me/articles/cli-telemetry-best-practices/) - Massimiliano Marcon
- [Log Analysis Using SQLite](https://drewcsillag.medium.com/log-analysis-using-sqlite-1cfdd40aa6f9) - Drew Csillag
- [sqlite-utils CLI](https://sqlite-utils.datasette.io/en/stable/cli.html) - Datasette

### Python CLI Tools
- [Click Documentation](https://click.palletsprojects.com/) - CLI framework
- [Rich Library](https://github.com/Textualize/rich) - Terminal formatting
- [tabulate](https://pypi.org/project/tabulate/) - ASCII tables

### Agent Skills
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Claude Docs
- [Report Generator Skill](https://claude-plugins.dev/skills/@PsAccelerator/Claude/Reports) - Template reference
- [Skill Creator Template](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) - Official template

### Structured Output
- [How to Get Consistent Structured Outputs](https://www.youtube.com/watch?v=dNpKQk5uxHw) - CrewAI tutorial
- [Structured Report Generation](https://github.com/langchain-ai/langchain-nvidia/blob/main/cookbook/structured_report_generation.ipynb) - LangChain
- [Smart Brevity Framework](https://web.storytell.ai/prompt/apply-the-smart-brevity-framework) - Concise communication

---

## Log de Cambios

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2025-12-31 | Plan inicial + investigación web completada | Elle |
| 2025-12-31 | Bug encontrado: `ctx sync -s .` falla por falta de `.resolve()` en cli.py:334 | Elle |
| 2025-12-31 | **Phase 1 COMPLETADA**: CLI commands implementados y probados | Elle |

---

## Implementación Completada

### ✅ Phase 1: CLI Commands (Completado 2025-12-31)

**Archivos creados**:
- `src/application/telemetry_reports.py` - Report generation
- `src/application/telemetry_charts.py` - ASCII charts

**Modificaciones**:
- `src/infrastructure/cli.py` - Agregado `telemetry_app` con 3 comandos

**Comandos funcionando**:
```bash
trifecta telemetry report -s . --last 30      # Reporte de tabla
trifecta telemetry export -s . --format json   # Exportar datos
trifecta telemetry chart -s . --type hits     # Gráfico ASCII
trifecta telemetry chart -s . --type latency  # Histograma
trifecta telemetry chart -s . --type commands # Bar chart
```

**Bug fix adicional**: El bug de `.resolve()` en cli.py:334 fue corregido (agregado automáticamente por linter/usuario).

### ✅ Phase 2: Agent Skill (Completado 2025-12-31)

**Ubicación**: `telemetry_analysis/skills/analyze/`

**Archivos creados**:
- `skill.md` - Template de output MANDATORY (max 50 líneas)
- `examples/basic_output.md` - Ejemplo de output

---

## Pendiente

- [ ] Tests unitarios para `telemetry_reports.py`
- [ ] Tests unitarios para `telemetry_charts.py`
- [ ] Integration tests para CLI commands

---

## Next Steps

1. ✅ **Investigación completada** - Stack tecnológico definido
2. ⏳ **Phase 1**: CLI commands (report, export, chart)
3. ⏳ **Phase 2**: Agent skill (telemetry-analyze)
4. ⏳ **Phase 3**: SQLite analytics (opcional)

---

**Última actualización**: 2025-12-31 @ Post web research
