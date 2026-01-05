### Task 6: ADR freeze for Router v1

**Files:**
- Create: `docs/adr/ADR_T9_ROUTER_V1.md`

**Step 1: Create ADR content**

Include:
- Scope: Router v1 for ctx.plan (PCC-only)
- Invariants: determinism, tie->fallback, true_zero_guidance=0, bundle assertions behavior
- Matching levels: L1/L2/L3/L4 definitions
- Scoring: exact=2, subset=1 + specificity + priority ordering
- Clamp: single-word support_terms rule (config-driven)
- Warnings taxonomy: weak_single_word_trigger, ambiguous_single_word_triggers, match_tie_fallback, bundle_assert_failed
- Gates: Core Gate-NL + Quality Gate (metrics + thresholds)
- Frozen for T10: changes require ADR update + re-run gates

---
