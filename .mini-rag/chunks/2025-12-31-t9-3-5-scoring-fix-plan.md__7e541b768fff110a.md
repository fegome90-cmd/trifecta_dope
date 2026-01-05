### Task 5: Regenerate T9.3.5 evaluation artifacts

**Files:**
- Modify: `docs/plans/t9_3_5_eval_report.md`
- Modify: `docs/plans/t9_3_5_confusions.md`

**Step 1: Re-run eval-plan**

Run:
```bash
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_5_after.txt
```

Expected: New output with updated distribution/accuracy.

**Step 2: Update reports**

Update `docs/plans/t9_3_5_eval_report.md` and `docs/plans/t9_3_5_confusions.md` using the new output, ensuring:
- Task #25 remains expected `observability_telemetry` per dataset.
- Before/after comparisons are consistent (no duplicated T9.3.4 data).
- Focused examples align with new debug info (score/specificity/priority/warnings).

---
