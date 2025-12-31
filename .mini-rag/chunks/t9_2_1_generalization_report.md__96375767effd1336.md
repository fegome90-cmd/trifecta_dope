## v1 vs v2 Comparison Table

| Metric | v1 (20 tasks) | v2 (40 tasks) | Delta |
|--------|--------------|--------------|-------|
| Plan hits | 17 (85.0%) | 24 (60.0%) | -25% |
| Plan misses | 3 (15.0%) | 16 (40.0%) | +25% |
| Zero hits | 0 (0%) | 0 (0%) | 0% |
| selected_by="alias" | 17 (85.0%) | 24 (60.0%) | -25% |
| selected_by="feature" | 0 (0%) | 0 (0%) | 0% |
| selected_by="fallback" | 3 (15.0%) | 16 (40%) | +25% |

**Analysis**: The 25% drop in plan_hit_rate indicates that triggers were overfitted to v1 phrasing patterns.

---
