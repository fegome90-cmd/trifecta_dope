### 1. L2 Ranking Change: Specificity Before Priority

**File**: `src/application/plan_use_case.py`

**Change**:
```python
# Sort by (score desc, specificity desc, priority desc)
filtered_candidates.sort(key=lambda x: (x[2], x[5], x[3]), reverse=True)
```

**Why**: Longer NL triggers should outrank single-word triggers at the same score.
