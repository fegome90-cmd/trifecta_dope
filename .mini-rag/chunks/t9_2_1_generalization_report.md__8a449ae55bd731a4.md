## Regression Test Coverage

```
tests/test_plan_use_case.py coverage:

test_plan_prefers_feature_over_alias_over_fallback    PASSED
test_plan_does_not_match_generic_triggers               PASSED
test_plan_returns_why_selected_by                       PASSED
test_repo_map_generation_is_capped_and_deterministic    PASSED
test_plan_fail_closed_on_invalid_feature                PASSED
test_plan_high_signal_trigger_matches_single_term        PASSED
```

**Caveat**: Coverage tests verify behavior but don't prevent overfitting.

---
