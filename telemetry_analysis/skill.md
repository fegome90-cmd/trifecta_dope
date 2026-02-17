---
name: trifecta_telemetry_analysis
description: Analyzes Trifecta CLI telemetry data from events.jsonl, metrics.json, and last_run.json to generate reports on usage, performance, and system health
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
  "ctx_build_count": N,              // Construcciones de pack
  "ctx_search_count": N,              // Búsquedas totales
  "ctx_search_hits_total": N,         // Resultados encontrados
  "ctx_search_zero_hits_count": N,    // Búsquedas sin resultados
  "ctx_get_count": N,                 // Recuperaciones de contexto
  "ctx_get_chunks_total": N,          // Chunks entregados
  "ctx_get_mode_excerpt_count": N,    // Modos excerpt vs raw
  "prime_links_included_total": N,    // Links en prime
  "ast_cache_hit_count": N,           // AST cache hits
  "ast_cache_miss_count": N,          // AST cache misses
  "ast_parse_count": N                // Total AST parses
}
```

### Event Schema (events.jsonl)
```json
{
  "ts": "ISO-8601",
  "run_id": "run_...",
  "segment_id": "...",
  "cmd": "ctx.search|ctx.get|ctx.sync|ast.symbols|telemetry.report",
  "args": {"query": "...", "limit": N, "segment": "."},
  "result": {"status": "ok|error", "hits": N, "error_code": "..."},
  "timing_ms": N,
  "warnings": [],
  "x": {}  // Extended metadata (cache_status, spanish_alias, etc.)
}
```

### AST Cache Events
- `ast.cache.hit` - Cache hit with backend info
- `ast.cache.miss` - Cache miss
- `ast.cache.write` - New entry written
- `ast.cache.lock_wait` - Waiting for file lock
- `ast.cache.lock_timeout` - Lock acquisition timeout

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

## CLI Commands

```bash
# Generate reports
trifecta telemetry report -s . --last 30          # Last 30 days
trifecta telemetry health -s .                    # System health check
trifecta telemetry export -s . --format json      # Export raw data
trifecta telemetry chart -s . --type hits         # ASCII chart: hits|latency|commands
```

## Analysis Commands (jq)

```bash
# Extract metrics from events.jsonl
jq -r '.cmd' events.jsonl | sort | uniq -c | sort -rn

# Average timing by command
jq -s 'group_by(.cmd) | map({cmd: .[0].cmd, avg: (map(.timing_ms) | add / length)})' events.jsonl

# Check for errors
jq 'select(.result.status != "ok")' events.jsonl

# Zero-hit searches rate
jq '[select(.cmd=="ctx.search")] | map(.result.hits==0) | length / length * 100' events.jsonl

# AST cache hit rate
jq '[select(.cmd=="ast.cache.hit")] | length' events.jsonl
jq '[select(.cmd=="ast.cache.miss")] | length' events.jsonl

# Spanish alias recovery events
jq 'select(.cmd=="ctx.search.spanish_alias")' events.jsonl
```

## Red Flags

| Pattern | Meaning | Action |
|---------|---------|--------|
| P95 > 2× P50 | Tail latency degradation | Investigate outliers |
| zero-hit > 40% | Poor search queries | Check query patterns |
| warnings recurring | Systemic issue | Fix root cause |
| pack stale | Context outdated | Rebuild pack |
| ast.cache.lock_timeout > 0 | File lock contention | Review concurrent access |
| cache_hit_rate < 50% | Poor cache utilization | Check cache configuration |

## Spanish Aliases Analysis

When analyzing search effectiveness, check for Spanish alias recovery:

```bash
# Check alias recovery success rate
jq 'select(.cmd=="ctx.search.spanish_alias" and .result.recovered==true)' events.jsonl

# Compare pass1 vs pass2 hits
jq 'select(.cmd=="ctx.search.spanish_alias") | {query: .args.query_preview, pass1: .result.pass1_hits, pass2: .result.pass2_hits}' events.jsonl
```

Metrics to track:
- **Recovery rate**: % of queries recovered via aliases
- **Hit improvement**: Average hit increase from pass1 to pass2
- **Top failed queries**: Spanish terms that still return zero hits

## Best Practices

1. **Start with Executive Summary** → Si se necesita detalle, ir a Performance Analysis
2. **Compare períodos** → Trends > snapshots absolutos
3. **Investigate outliers** → Un evento malo puede sesgar P95
4. **Correlate metrics** → latency vs search effectiveness vs errors
5. **Check AST cache** → Verify cache_hit_count increases with repeated symbol extraction
6. **Monitor Spanish aliases** → Ensure recovery rate > 60% for Spanish queries

## Related Skills

- `trifecta_dope` - Main Trifecta skill for context operations
- `telemetry_analysis/skills/analyze` - Concise telemetry report generation

## References

- [CLI Telemetry Best Practices](https://marcon.me/articles/cli-telemetry-best-practices/)
- [P50/P95/P99 Latency Guide](https://oneuptime.com/blog/post/2025-09-15-p50-vs-p95-vs-p99-latency-percentiles/view)
- [Agent Monitoring Patterns](https://www.requesty.ai/solution/detailed-analytics)
- Trifecta Documentation: `docs/telemetry/`
