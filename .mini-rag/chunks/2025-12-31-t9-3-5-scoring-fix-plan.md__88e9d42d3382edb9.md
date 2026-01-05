### Task 6: Full test sweep + commit

**Files:**
- Modify: `tests/test_plan_use_case.py`
- Modify: `src/application/plan_use_case.py`
- Modify: `docs/plans/t9_3_5_eval_report.md`
- Modify: `docs/plans/t9_3_5_confusions.md`

**Step 1: Run full test suite**

Run:
```bash
uv run pytest
```

Expected: PASS.

**Step 2: Commit**

Run:
```bash
git add tests/test_plan_use_case.py src/application/plan_use_case.py \
  docs/plans/t9_3_5_eval_report.md docs/plans/t9_3_5_confusions.md
git commit -m "fix: align L2 clamp and eval evidence for T9.3.5"
```

---

Plan complete and saved to `docs/plans/2025-12-31-t9-3-5-scoring-fix-plan.md`. Two execution options:

1. Subagent-Driven (this session) — I dispatch a fresh subagent per task, review between tasks, fast iteration  
2. Parallel Session (separate) — Open new session with executing-plans, batch execution with checkpoints

Which approach?
