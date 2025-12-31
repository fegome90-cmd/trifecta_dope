# T9.3.5 Scoring Fix Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix L2 scoring clamp + telemetry/debug reporting per T9.3.5 spec, then regenerate eval artifacts with consistent evidence.

**Architecture:** Keep core L2 matching deterministic. Add temporary instrumentation for diagnosis, then remove it. Make clamp behavior explicit when blocking top single-word triggers, and compute top_k after sorting.

**Tech Stack:** Python 3.12+, Typer CLI, Pytest, Mini-RAG CLI.

---

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

### Task 2: Add failing unit tests for L2 clamp + specificity ranking

**Files:**
- Modify: `tests/test_plan_use_case.py`

**Step 1: Write failing tests**

Add tests (examples below) that use schema_version 3 with `nl_triggers`:
```python
def test_l2_specificity_beats_priority_for_multiword_trigger(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "telemetry_feature": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            },
            "symbol_surface": {
                "priority": 2,
                "nl_triggers": ["telemetry class"],
                "bundle": {"chunks": ["c2"], "paths": ["p2.py"]},
            },
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (tmp_path / "p2.py").write_text("# p2")
    (ctx_dir / "prime_test.md").write_text("# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |")

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "how is the telemetry class constructed")
    assert result["selected_feature"] == "symbol_surface"
    assert result["selected_by"] == "nl_trigger"

def test_l2_single_word_clamp_blocks_without_support_terms(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "telemetry_feature": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            }
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (ctx_dir / "prime_test.md").write_text("# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |")

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "telemetry")
    assert result["selected_by"] == "fallback"
    assert result["l2_warning"] == "weak_single_word_trigger"
```

**Step 2: Run the new tests to confirm they fail**

Run:
```bash
uv sync --extra dev
uv run pytest tests/test_plan_use_case.py::test_l2_specificity_beats_priority_for_multiword_trigger -v
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_clamp_blocks_without_support_terms -v
```

Expected: FAIL (current implementation doesn’t set warning on clamp and ranking may not select multiword correctly).

---

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
