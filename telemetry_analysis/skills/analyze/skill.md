---
name: trifecta_telemetry_analysis
description: Analyzes Trifecta CLI telemetry data and generates concise reports with metrics, command statistics, and insights. Use when user asks to analyze telemetry from a Trifecta segment.
---

# Trifecta Telemetry Analysis

Analyzes Trifecta CLI telemetry and generates concise report.

## Usage

When user asks to analyze telemetry from a Trifecta segment:

1. Read telemetry data from `<segment>/_ctx/telemetry/events.jsonl`
2. Calculate metrics (command counts, hit rate, latency)
3. Generate report using EXACT format below

## Telemetry Event Structure

Events are JSON lines with this schema:
- `ts`: ISO8601 timestamp
- `cmd`: Command name (ctx.search, ctx.sync, ast.symbols, etc.)
- `result.hits`: Number of search hits (for ctx.search)
- `timing_ms`: Execution time in milliseconds
- `args`: Command arguments
- `status`: Result status (success/error)

## Output Format (MANDATORY - ALWAYS USE THIS)

```markdown
## Summary
| Metric | Value |
|--------|-------:|
| Commands | N |
| Searches | N |
| Hit rate | X% |
| Avg latency | Nms |

## Top Commands
| Command | Count | % |
|---------|------:|---:|
| ctx.search | N | NN% |
| ctx.sync | N | NN% |

## Insights
- ✅/⚠️ One insight per line
- Max 5 insights
- Max 50 lines total
```

## Rules

1. **Max 50 lines total** - Never exceed
2. **Only tables** - No paragraphs, no explanations
3. **Max 5 insights** - Bullet points only
4. **No fluff** - Direct data only
5. **No intro/outro** - Start with table, end with insights

## Examples

See `examples/basic_output.md` for reference output format.

### Example Insights
- ✅ Low average latency (< 5ms)
- ⚠️ High zero-hit rate (> 50%)
- ✅ Strong cache hit rate (> 80%)
- ⚠️ Elevated error rate in ctx.sync
- ✅ Spanish alias recovery working well
