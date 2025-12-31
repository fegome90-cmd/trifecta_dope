---
name: telemetry_analysis
description: Use when analyzing Trifecta CLI telemetry data (events.jsonl, metrics.json, last_run.json) to generate concise reports
---

## Overview

Telemetría local-first para análisis de uso del CLI Trifecta.

**Ubicación**: `_ctx/telemetry/` en cada segmento

**Archivos**:
- `events.jsonl` - Log crudo de eventos (rotación 5MB)
- `metrics.json` - Contadores acumulados
- `last_run.json` - Resumen del último run

## Métricas Clave

### Latency Percentiles
| Métrica | Significado |
|---------|-------------|
| **P50** | Latencia típica del usuario |
| **P95** | Early warning de degradación |
| **P99** | Tail latencia crítica |
| **max_ms** | Peor caso observado |

### Counters (metrics.json)
```json
{
  "ctx_build_count": N,           // Construcciones de pack
  "ctx_search_count": N,           // Búsquedas totales
  "ctx_search_hits_total": N,      // Resultados encontrados
  "ctx_search_zero_hits_count": N, // Búsquedas sin resultados
  "ctx_get_count": N,              // Recuperaciones de contexto
  "ctx_get_chunks_total": N,       // Chunks entregados
  "ctx_get_mode_excerpt_count": N, // Modos excerpt vs raw
  "prime_links_included_total": N  // Links en prime
}
```

### Event Schema (events.jsonl)
```json
{
  "ts": "ISO-8601",
  "run_id": "run_...",
  "cmd": "ctx.search|ctx.get|load|ctx.build",
  "args": {"query": "...", "limit": N},
  "result": {"status": "ok|validation_failed", "hits": N},
  "timing_ms": N,
  "warnings": []
}
```

## Report Templates

### Template 1: Executive Summary (1-2 min)
```markdown
## CLI Usage Summary - [Period]

**Commands**: N total | [Top commands by %]
**Latency**: P50=Xms, P95=Yms
**Errors**: N failures | Top: [error types]
**Key Insight**: [Single most important finding]
```

### Template 2: Performance Analysis
```markdown
## Performance Report

### Latency Distribution
- ctx.search: P50=Xms, P95=Yms, max=Zms
- ctx.get: P50=Xms, P95=Yms
- ctx.build: P50=Xms

### Search Effectiveness
- Hit rate: hits/total = X%
- Zero-hit searches: N (Y%)
- Top query patterns: [...]

### Pack State
- SHA: [hash] | Age: [time] | Stale: [bool]
```

### Template 3: Trend Analysis (Multi-period)
```markdown
## Usage Trends [Period 1] vs [Period 2]

**Growth**: +X% commands | +Y% active runs
**Performance**: P50 changed Xms | P95 changed Yms
**Patterns**: [New behaviors, regression warnings]
```

## Analysis Commands

```bash
# Extract metrics from events.jsonl
jq -r '.cmd' events.jsonl | sort | uniq -c | sort -rn

# Average timing by command
jq -s 'group_by(.cmd) | map({cmd: .[0].cmd, avg: (map(.timing_ms) | add / length)})' events.jsonl

# Check for errors
jq 'select(.result.status != "ok")' events.jsonl

# Zero-hit searches rate
jq '[select(.cmd=="ctx.search")] | map(.result.hits==0) | length / length * 100' events.jsonl
```

## Red Flags

| Pattern | Meaning | Action |
|---------|---------|--------|
| P95 > 2× P50 | Tail latency degradation | Investigate outliers |
| zero-hit > 40% | Poor search queries | Check query patterns |
| warnings recurring | Systemic issue | Fix root cause |
| pack stale | Context outdated | Rebuild pack |

## Best Practices

1. **Start with Executive Summary** → Si se necesita detalle, ir a Performance Analysis
2. **Compare períodos** → Trends > snapshots absolutos
3. **Investigate outliers** → Un evento malo puede sesgar P95
4. **Correlate metrics** → latency vs search effectiveness vs errors

## References

- [CLI Telemetry Best Practices](https://marcon.me/articles/cli-telemetry-best-practices/)
- [P50/P95/P99 Latency Guide](https://oneuptime.com/blog/post/2025-09-15-p50-vs-p95-vs-p99-latency-percentiles/view)
- [Agent Monitoring Patterns](https://www.requesty.ai/solution/detailed-analytics)
