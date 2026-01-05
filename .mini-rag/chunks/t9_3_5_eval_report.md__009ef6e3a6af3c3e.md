## Executive Summary

| Gate | Status | accuracy_top1 | fallback_rate | alias_rate | nl_trigger_rate |
|------|--------|---------------|---------------|------------|-----------------|
| **Core Gate-NL** | ❌ **NO-GO** | 70.0% | 22.5% >= 20% ❌ | 35.0% <= 70% ✅ | 42.5% |

**Overall Decision**: ❌ **T9.3.5 NO-GO** — fallback rate regressed and accuracy dropped.

**Key Outcomes**:
- Single-word clamp applied (Task #25 "telemetry" now falls back as expected)
- L2 specificity ranking in place (score, specificity, priority)
- **symbol_surface regressed**: TP=2 → 0 (Tasks #17, #35 now fallback)

**Constraints Adhered To**:
- NO new nl_triggers added
- NO aliases.yaml edits
- NO dataset changes
- NO threshold changes
- NO embeddings/stemming

---
