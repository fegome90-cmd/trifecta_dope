**Step 2: Run the new tests to confirm they fail**

Run:
```bash
uv sync --extra dev
uv run pytest tests/test_plan_use_case.py::test_l2_specificity_beats_priority_for_multiword_trigger -v
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_clamp_blocks_without_support_terms -v
```

Expected: FAIL (current implementation doesn’t set warning on clamp and ranking may not select multiword correctly).

---
