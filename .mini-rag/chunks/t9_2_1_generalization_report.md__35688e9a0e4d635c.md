### 4. Regression Tests
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run pytest tests/test_plan_use_case.py -v
```

**Output**:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 6 items

tests/test_plan_use_case.py::test_plan_prefers_feature_over_alias_over_fallback PASSED [ 16%]
tests/test_plan_use_case.py::test_plan_does_not_match_generic_triggers PASSED [ 33%]
tests/test_plan_use_case.py::test_plan_returns_why_selected_by PASSED [ 50%]
tests/test_plan_use_case.py::test_repo_map_generation_is_capped_and_deterministic PASSED [ 66%]
tests/test_plan_use_case.py::test_plan_fail_closed_on_invalid_feature PASSED [ 83%]
tests/test_plan_use_case.py::test_plan_high_signal_trigger_matches_single_term PASSED [100%]

============================== 6 passed in 0.05s ===============================
```
