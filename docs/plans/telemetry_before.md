# Telemetry Diagnostic - BEFORE

**Generated**: 2025-12-31  
**Command**: `python3 scripts/telemetry_diagnostic.py`

## Resumen General

| Métrica | Valor |
|---------|-------|
| total_searches | 19 |
| hits | 6 |
| zero_hits | 13 |
| hit_rate | 31.6% |
| avg_latency_ms | 0.0 |

## Top Zero-Hit Queries (Top 10)

| Count | Query |
|-------|-------|
| 2 | parser |
| 1 | test |
| 1 | alias expansion telemetry |
| 1 | roadmap pending tasks |
| 1 | find |
| 1 | documentation plans walkthroughs |
| 1 | sequential think planning methodology |
| 1 | deprecación CLI oficial |
| 1 | report generate table output |
| 1 | cli command group typer |

## Breakdown por Query Type

| Type | Count | % |
|------|-------|---|
| unknown | 17 | 89.5% |
| meta | 1 | 5.3% |
| impl | 1 | 5.3% |

## Breakdown por Hit Target

| Target | Count | % |
|--------|-------|---|
| agent | 3 | 21.4% |
| session | 5 | 35.7% |
| ref | 6 | 42.9% |

## Heurística de Clasificación

### Query Type
- **meta**: how/what/where/plan/guide/architecture/design/status
- **impl**: function/class/method/file/implement/code/symbol
- **unknown**: no clasificable

### Hit Target
Basado en prefix del chunk_id:
- `skill:*` → skill
- `prime:*` → prime
- `session:*` → session
- `agent:*` → agent
- `ref:*` → ref
- other → other
