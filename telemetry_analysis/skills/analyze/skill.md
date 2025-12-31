# Trifecta Telemetry Analysis

Analyzes Trifecta CLI telemetry and generates concise report.

## Usage

When user asks to analyze telemetry from a Trifecta segment:

1. Read telemetry data from `<segment>/_ctx/telemetry/events.jsonl`
2. Calculate metrics (command counts, hit rate, latency)
3. Generate report using EXACT format below

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

See `examples/` directory for reference outputs.
