### Task 7: Full test sweep + commit

**Files:**
- Modify: `_ctx/aliases.yaml`
- Modify: `src/application/plan_use_case.py`
- Modify: `tests/test_plan_use_case.py`
- Modify: `docs/plans/t9_3_6_clamp_calibration.md`
- Create: `docs/adr/ADR_T9_ROUTER_V1.md`

**Step 1: Run full test suite**

Run:
```bash
uv run pytest
```
Expected: PASS.

**Step 2: Commit**

Run:
```bash
git add _ctx/aliases.yaml src/application/plan_use_case.py tests/test_plan_use_case.py \
  docs/plans/t9_3_6_clamp_calibration.md docs/adr/ADR_T9_ROUTER_V1.md

git commit -m "feat: calibrate clamp and freeze Router v1"
```

---

Plan complete and saved to `docs/plans/2025-12-31-t9-3-6-clamp-calibration-plan.md`. Two execution options:

1. Subagent-Driven (this session) — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) — Open new session with executing-plans, batch execution with checkpoints

Which approach?
