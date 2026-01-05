### Task 3: Implement L2 clamp + top_k fixes (plus temporary instrumentation)

**Files:**
- Modify: `src/application/plan_use_case.py`

**Step 1: Add temporary debug instrumentation**

Add a temporary `debug_trace` list for L2 decisions and include it in return only when an env flag like `TRIFECTA_L2_DEBUG=1` is present. This is temporary for diagnosis.

**Step 2: Implement clamp behavior**

When a single-word candidate is blocked for missing support terms:
- If it was the top candidate (by score/specificity/priority), force fallback with:
  - `warning="weak_single_word_trigger"`
  - `debug_info["blocked"]=True`
  - `debug_info["block_reason"]="missing_support_term"`
  - `debug_info["support_terms_present"]=[]` (or terms found)

**Step 3: Fix top_k ordering**

Build `top_k` from the sorted candidate list (after filtering), not during iteration.

**Step 4: Plumb telemetry fields**

Ensure `execute()` sets `l2_blocked` and `l2_block_reason` from `debug_info` so telemetry shows the clamp/tie decisions.

**Step 5: Run the tests**

Run:
```bash
uv run pytest tests/test_plan_use_case.py::test_l2_specificity_beats_priority_for_multiword_trigger -v
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_clamp_blocks_without_support_terms -v
```

Expected: PASS.

---
