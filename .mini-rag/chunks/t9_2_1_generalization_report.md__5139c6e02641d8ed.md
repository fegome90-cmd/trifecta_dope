### 2. Evaluation v2 on trifecta_dope
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2.md
```

**Output**:
```
============================================================
EVALUATION REPORT: ctx.plan
============================================================
Dataset: docs/plans/t9_plan_eval_tasks_v2.md
Segment: .
Total tasks: 40

Results:
  Plan hits:   24 (60.0%)
  Plan misses: 16 (40.0%)

Selection Method Distribution:
  feature: 0 (0.0%)
  alias: 24 (60.0%)
  fallback: 0 (0.0%)

Top Missed Tasks:
  1. can you show me the token counting logic
  2. explain how primes organize the reading list
  3. walk through the chunk retrieval flow
  4. locate the GetChunkUseCase implementation
  5. where is the event flush mechanism defined

Examples (task → selected_feature → returned):
  • 'where would i find stats about search performance'
    → observability_telemetry (6 chunks, 3 paths)
  • 'i need to design a ctx export feature'
    → observability_telemetry (6 chunks, 3 paths)
  • 'what does the clean architecture look like here'
    → arch_overview (4 chunks, 2 paths)

❌ NO-GO: plan_miss_rate 40.0% >= 20%
```
