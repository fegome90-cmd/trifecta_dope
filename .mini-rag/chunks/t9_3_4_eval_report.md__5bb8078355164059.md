### 2. Vague Queries → Fallback vs Overmatch

**Issue**: Tasks #4, #8 ("i need to design a ctx export feature", "help me create a ctx trends command") expected fallback but match observability_telemetry.

**Root Cause**: "ctx" term triggers high-priority single-word matches; L2 lacks "design" or "create" intent patterns.

**Impact**: 2 FP for observability_telemetry (from fallback)

**Decision for T9.3.4**: Accept as expected behavior; vague "design/create" queries without domain context reasonably match high-priority triggers.

---
