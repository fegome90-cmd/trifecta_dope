### 4. Telemetry Enhancements

**File**: `src/application/plan_use_case.py`

```python
# T9.3.3: Include L2 matching details
if result.get("l2_warning"):
    telemetry_attrs["l2_warning"] = result["l2_warning"]
if result.get("l2_score") > 0:
    telemetry_attrs["l2_score"] = result["l2_score"]
if result.get("l2_match_mode"):
    telemetry_attrs["l2_match_mode"] = result["l2_match_mode"]
```

---
