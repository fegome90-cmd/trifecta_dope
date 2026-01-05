### Task 4: Remove temporary instrumentation

**Files:**
- Modify: `src/application/plan_use_case.py`

**Step 1: Remove debug-only blocks**

Delete temporary debug tracing (anything gated by `TRIFECTA_L2_DEBUG`) to keep code clean.

**Step 2: Re-run tests**

Run:
```bash
uv run pytest tests/test_plan_use_case.py::test_l2_specificity_beats_priority_for_multiword_trigger -v
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_clamp_blocks_without_support_terms -v
```

Expected: PASS.

---
