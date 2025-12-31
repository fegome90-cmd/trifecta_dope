### 1. Priority Hierarchy vs Specificity

**Issue**: symbol_surface.nl_triggers "telemetry class" (priority 2) cannot outrank observability_telemetry.nl_triggers "telemetry" (priority 4) for Tasks #17, #35.

**Root Cause**: L2 matching sorts by (score, priority desc), not by trigger specificity (length).

**Impact**: 2 FN remain for symbol_surface

**Potential Future Fix**:
- Option A: Increase symbol_surface.priority to 4 (but need to audit all symbol_surface triggers)
- Option B: Enhance L2 matching to prefer longer triggers within same score tier

**Decision for T9.3.4**: Document as known limitation; focus on bounded patches for high-impact fixes.
