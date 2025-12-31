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
