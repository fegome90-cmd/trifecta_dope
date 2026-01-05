### NL Metrics Table

| Metric | Before | After | Delta | Target (Core Gate-NL) | Status |
|--------|--------|-------|-------|------------------------|--------|
| plan_accuracy_top1 | 72.5% | **70.0%** | -2.5% | N/A | ❌ Regression |
| nl_trigger_hit_rate | 50.0% | **42.5%** | -7.5% | N/A | ℹ️ Changed |
| alias_hit_rate | 35.0% | **35.0%** | 0.0% | <= 70% | ✅ **PASS** |
| fallback_rate | 15.0% | **22.5%** | +7.5% | < 20% | ❌ **FAIL** |
| true_zero_guidance_rate | 0.0% | 0.0% | — | = 0% | ✅ **PASS** |
| feature_hit_rate | 0.0% | 0.0% | — | >= 10% (informative) | ✗ Below |
