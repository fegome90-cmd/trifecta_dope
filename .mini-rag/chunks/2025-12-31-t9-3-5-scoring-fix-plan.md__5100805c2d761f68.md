### Task 1: Baseline diagnosis (Mini-RAG + eval-plan output capture)

**Files:**
- Read: `docs/plans/t9_3_5_eval_report.md`
- Read: `docs/plans/t9_3_5_confusions.md`
- Read: `docs/plans/t9_plan_eval_tasks_v2_nl.md`

**Step 1: Use Mini-RAG to locate prior evidence**

Run:
```bash
mini-rag query "T9.3.5 scoring fix L2 clamp specificity"
```

Expected: Output includes chunks referencing `t9_3_5_eval_report` and plan details.

**Step 2: Capture current eval output (before changes)**

Run:
```bash
mkdir -p tmp_plan_test
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_5_before.txt
```

Expected: `EVALUATION REPORT: ctx.plan` in output; file `tmp_plan_test/t9_3_5_before.txt` created.

---
