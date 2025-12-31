#### D2) Baseline con ctx.search

```bash
for task in "${tasks[@]}"; do
  trifecta ctx search -s . --query "$task" --limit 5
done | tee baseline_results.txt
```

Métricas:
- % zero_hits
- % hits
