# Executive Summary Template

**Period**: {{start_date}} to {{end_date}}
**Segment**: {{segment_name}}
**Generated**: {{generated_at}}

## 📊 Usage Overview

| Metric | Value |
|--------|-------|
| Total Commands | {{total_commands}} |
| Active Runs | {{active_runs}} |
| Unique Commands | {{unique_commands}} |

### Command Distribution
| Command | Count | % |
|---------|-------|---|
| {{cmd_name}} | {{count}} | {{pct}}% |
| ... | ... | ... |

## ⚡ Performance

| Metric | P50 | P95 | Max |
|--------|-----|-----|-----|
| ctx.search | {{p50}}ms | {{p95}}ms | {{max}}ms |
| ctx.get | {{p50}}ms | {{p95}}ms | {{max}}ms |
| ctx.build | {{p50}}ms | {{p95}}ms | {{max}}ms |

## ⚠️ Errors & Warnings

- **Total Errors**: {{error_count}}
- **Error Rate**: {{error_rate}}%
- **Top Issues**:
  1. {{issue_1}} ({{count_1}})
  2. {{issue_2}} ({{count_2}})
  3. {{issue_3}} ({{count_3}})

## 💡 Key Insights

{{key_insight_1}}
{{key_insight_2}}
{{key_insight_3}}

## 📈 Trends

- {{trend_1}}
- {{trend_2}}
- {{trend_3}}

---

## Recommendations

{{recommendation_1}}
{{recommendation_2}}
