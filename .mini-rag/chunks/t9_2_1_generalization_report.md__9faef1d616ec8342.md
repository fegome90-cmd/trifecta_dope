## Executive Summary

| Dataset | Plan Hit Rate | Plan Miss Rate | Zero Hit Rate | Gate |
|---------|--------------|----------------|---------------|------|
| v1 (trifecta_dope) | 85.0% (17/20) | 15.0% (3/20) | 0% | ✅ GO |
| v2 (trifecta_dope) | 60.0% (24/40) | 40.0% (16/40) | 0% | ❌ NO-GO |
| v2 (AST) | 0.0% (0/40) | 100.0% (40/40) | 0% | ❌ NO-GO |

**Conclusion**: The v1 results were **overfitted** to specific phrasing patterns. When tested with v2 (same domain, different phrasing), plan_miss_rate increased from 15% to 40%, failing the <20% threshold.

---
