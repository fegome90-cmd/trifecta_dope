# Trifecta Telemetry Analysis

> **Centralización de análisis de telemetría para el proyecto Trifecta Dope**

Esta carpeta NO se instala con cada Trifecta. Es un hub centralizado para analizar datos de telemetría de cualquier segmento.

## 📁 Estructura

```
telemetry_analysis/
├── skill.md          # Skill para agentes (templates de reportes)
├── templates/        # Templates de reportes pre-generados
├── scripts/          # Scripts de análisis
└── README.md         # Este archivo
```

## 🎯 Uso

### Desde un Agente Claude

```markdown
@telemetry_analysis/skill.md

Por favor genera un Executive Summary de la telemetría de /ruta/al/segmento
```

### Manual (CLI)

```bash
# Análisis rápido de un segmento
cd /ruta/al/segmento
python /ruta/a/trifecta_dope/telemetry_analysis/scripts/analyze.py

# Reporte ejecutivo
python /ruta/a/trifecta_dope/telemetry_analysis/scripts/report.py --executive
```

## 📊 Métricas Disponibles

| Archivo | Contenido | Granularidad |
|---------|-----------|--------------|
| `events.jsonl` | Eventos crudos | Por comando |
| `metrics.json` | Contadores | Acumulado |
| `last_run.json` | Última ejecución | Run-level |

## 🔍 Análisis Comunes

### 1. Executive Summary
- Commands totales
- Top comandos por uso
- Latencias P50/P95
- Errores principales

### 2. Performance Deep Dive
- Latencias por comando
- Search effectiveness rate
- Zero-hit analysis
- Pack state check

### 3. Trend Analysis
- Comparación entre períodos
- Crecimiento de uso
- Degradación de performance

## 🛠️ Scripts

| Script | Descripción |
|--------|-------------|
| `analyze.py` | Análisis básico con jq/python |
| `report.py` | Generación de reportes formateados |
| `trends.py` | Comparación entre períodos |

## 📚 Referencias

- [CLI Telemetry Best Practices](https://marcon.me/articles/cli-telemetry-best-practices/)
- [P50/P95/P99 Latency Guide](https://oneuptime.com/blog/post/2025-09-15-p50-vs-p95-vs-p99-latency-percentiles/view)
- [Agent Monitoring Patterns](https://www.requesty.ai/solution/detailed-analytics)
