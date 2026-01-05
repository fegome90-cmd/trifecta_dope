### Task 1: Capture T9.3.4 vs T9.3.5 baselines (no dataset changes)

**Files:**
- Read: `docs/plans/t9_plan_eval_tasks_v2_nl.md`
- Create: `tmp_plan_test/t9_3_4_baseline.txt`
- Create: `tmp_plan_test/t9_3_5_current.txt`
- Create: `tmp_plan_test/t9_3_4_baseline_tasks.json`
- Create: `tmp_plan_test/t9_3_5_current_tasks.json`

**Step 1: Verify dataset identity (no edits)**

Run:
```bash
sha256sum docs/plans/t9_plan_eval_tasks_v2_nl.md
```
Expected: hash remains constant throughout.

**Step 2: Run baseline eval (T9.3.4)**

From `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-4-baseline`:
```bash
uv run trifecta ctx eval-plan -s . --dataset /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration/docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_4_baseline.txt
```
Expected: `EVALUATION REPORT: ctx.plan` output and file created.

**Step 3: Run current eval (T9.3.5)**

From `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration`:
```bash
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_5_current.txt
```
Expected: `EVALUATION REPORT: ctx.plan` output and file created.

**Step 4: Generate per-task predictions (baseline + current)**

Baseline worktree:
