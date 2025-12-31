## Executive Summary

| Gate | Status | fallback_rate | alias_hit_rate | feature_hit_rate | true_zero_guidance |
|------|--------|--------------|----------------|-----------------|-------------------|
| **Gate-NL** | ❌ NO-GO | 17.5% < 20% ✓ | 82.5% > 70% ✗ | 0.0% < 10% ✗ | 0.0% = 0% ✓ |
| **Gate-L1** | ✅ GO | 0.0% <= 5% ✓ | N/A | 100.0% >= 95% ✓ | 0.0% = 0% ✓ |

**Overall Decision**:
- **Gate-L1**: ✅ **GO** - All criteria passed
- **Gate-NL**: ❌ **NO-GO** - alias_hit_rate exceeds threshold (good generalization but over-matching)

---
