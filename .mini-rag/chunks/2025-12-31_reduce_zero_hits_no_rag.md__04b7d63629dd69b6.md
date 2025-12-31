#### D3) Evaluación con ctx.plan

```bash
for task in "${tasks[@]}"; do
  trifecta ctx.plan -s . --task "$task"
done | tee plan_results.txt
```

Métricas:
- % plan_hit
- % zero_hits resultante (search puede seguir igual)
