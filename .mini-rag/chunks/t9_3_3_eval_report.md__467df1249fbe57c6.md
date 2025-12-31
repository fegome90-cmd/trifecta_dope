### 3. Result Dictionary Updates

**File**: `src/application/plan_use_case.py` (execute method)

```python
result = {
    "selected_feature": None,
    "plan_hit": False,
    "selected_by": None,
    "match_terms_count": 0,
    "matched_trigger": None,
    "l2_warning": None,      # NEW: L2 warnings
    "l2_score": 0,          # NEW: L2 match score
    "l2_match_mode": None,   # NEW: "exact" | "subset" | None
    # ... rest of fields
}
```
