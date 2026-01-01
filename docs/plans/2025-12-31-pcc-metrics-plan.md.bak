# PCC Tool-Calling Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend `trifecta ctx eval-plan` to output PCC tool-calling metrics (path correctness, safe vs false fallback, guardrails) using PRIME feature_map, and document the spec in an ADR.

**Architecture:** Add a small PCC metrics helper to parse PRIME `index.feature_map`, then compute per-task PCC outcomes using existing eval-plan results (selected_feature, paths, selected_by). Keep dataset unchanged.

**Tech Stack:** Python 3.12+, Typer CLI, Pytest, Markdown ADR.

---

### Task 1: Add PCC metrics helpers (TDD)

**Files:**
- Create: `src/application/pcc_metrics.py`
- Test: `tests/unit/test_pcc_metrics.py`

**Step 1: Write failing tests for PRIME feature_map parsing**

Create `tests/unit/test_pcc_metrics.py`:
```python
from pathlib import Path

from src.application.pcc_metrics import parse_feature_map


def test_parse_feature_map_paths(tmp_path: Path) -> None:
    prime = tmp_path / "prime_test.md"
    prime.write_text(
        """
### index.feature_map
| Feature | Chunk IDs | Paths | Keywords |
|---------|-----------|-------|----------|
| telemetry | `skill:*` | `README.md`, `src/infrastructure/telemetry.py` | telemetry |
| context_pack | `skill:*` | `src/application/use_cases.py` | context pack |
"""
    )

    feature_map = parse_feature_map(prime)

    assert feature_map["telemetry"] == ["README.md", "src/infrastructure/telemetry.py"]
    assert feature_map["context_pack"] == ["src/application/use_cases.py"]
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_parse_feature_map_paths -v
```
Expected: FAIL (module/functions missing).

**Step 3: Implement minimal parser**

Create `src/application/pcc_metrics.py`:
```python
from __future__ import annotations

from pathlib import Path


def parse_feature_map(prime_path: Path) -> dict[str, list[str]]:
    content = prime_path.read_text()
    lines = content.splitlines()
    feature_map: dict[str, list[str]] = {}

    in_table = False
    for line in lines:
        if line.strip().startswith("### index.feature_map"):
            in_table = True
            continue
        if in_table and line.strip().startswith("### "):
            break
        if in_table and line.strip().startswith("|") and "Feature" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 3:
                feature = cols[0]
                paths_raw = cols[2]
                paths = [p.strip().strip("`") for p in paths_raw.split(",") if p.strip()]
                feature_map[feature] = paths

    return feature_map
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_parse_feature_map_paths -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add src/application/pcc_metrics.py tests/unit/test_pcc_metrics.py
git commit -m "feat: add PCC feature_map parser"
```

---

### Task 2: Compute PCC metrics per task (TDD)

**Files:**
- Modify: `src/application/pcc_metrics.py`
- Test: `tests/unit/test_pcc_metrics.py`

**Step 1: Add failing test for PCC evaluation**

Append to `tests/unit/test_pcc_metrics.py`:
```python
from src.application.pcc_metrics import evaluate_pcc


def test_evaluate_pcc_path_correctness() -> None:
    feature_map = {"telemetry": ["src/infrastructure/telemetry.py"]}

    result = evaluate_pcc(
        expected_feature="telemetry",
        predicted_feature="telemetry",
        predicted_paths=["src/infrastructure/telemetry.py"],
        feature_map=feature_map,
        selected_by="nl_trigger",
    )

    assert result["path_correct"] is True
    assert result["false_fallback"] is False
    assert result["safe_fallback"] is False
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_evaluate_pcc_path_correctness -v
```
Expected: FAIL.

**Step 3: Implement minimal PCC evaluation**

In `src/application/pcc_metrics.py`:
```python
def evaluate_pcc(
    expected_feature: str,
    predicted_feature: str | None,
    predicted_paths: list[str],
    feature_map: dict[str, list[str]],
    selected_by: str,
) -> dict[str, bool]:
    expected_paths = feature_map.get(expected_feature, []) if expected_feature != "fallback" else []
    path_correct = bool(
        expected_feature != "fallback"
        and predicted_feature == expected_feature
        and any(p in expected_paths for p in predicted_paths)
    )

    false_fallback = expected_feature != "fallback" and selected_by == "fallback"
    safe_fallback = expected_feature == "fallback" and selected_by == "fallback"

    return {
        "path_correct": path_correct,
        "false_fallback": false_fallback,
        "safe_fallback": safe_fallback,
    }
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_evaluate_pcc_path_correctness -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add src/application/pcc_metrics.py tests/unit/test_pcc_metrics.py
git commit -m "feat: add PCC evaluation helper"
```

---

### Task 3: Extend eval-plan output with PCC metrics (TDD)

**Files:**
- Modify: `src/infrastructure/cli.py`
- Test: `tests/unit/test_pcc_metrics.py`

**Step 1: Add failing test for eval-plan PCC summary**

Append to `tests/unit/test_pcc_metrics.py`:
```python
from src.application.pcc_metrics import summarize_pcc


def test_summarize_pcc_counts() -> None:
    rows = [
        {"path_correct": True, "false_fallback": False, "safe_fallback": False},
        {"path_correct": False, "false_fallback": True, "safe_fallback": False},
    ]

    summary = summarize_pcc(rows)
    assert summary["path_correct_count"] == 1
    assert summary["false_fallback_count"] == 1
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_summarize_pcc_counts -v
```
Expected: FAIL.

**Step 3: Implement summarize_pcc helper**

In `src/application/pcc_metrics.py`:
```python
def summarize_pcc(rows: list[dict[str, bool]]) -> dict[str, int]:
    return {
        "path_correct_count": sum(1 for r in rows if r.get("path_correct")),
        "false_fallback_count": sum(1 for r in rows if r.get("false_fallback")),
        "safe_fallback_count": sum(1 for r in rows if r.get("safe_fallback")),
    }
```

**Step 4: Update eval-plan to compute PCC metrics**

In `src/infrastructure/cli.py`:
- Load PRIME: `prime_*.md` from `_ctx` (choose expected one if available)
- Parse feature_map via `parse_feature_map`
- For each task result, compute PCC metrics using `evaluate_pcc`
- Print a new section:
  - `PCC Metrics:`
    - `path_correct_count`, `false_fallback_count`, `safe_fallback_count`

**Step 5: Run tests to verify pass**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py -v
```
Expected: PASS.

**Step 6: Commit**

```bash
git add src/infrastructure/cli.py src/application/pcc_metrics.py tests/unit/test_pcc_metrics.py
git commit -m "feat: add PCC metrics to eval-plan"
```

---

### Task 4: ADR for PCC metrics

**Files:**
- Create: `docs/adr/ADR_PCC_METRICS.md`

**Step 1: Draft ADR**

Include:
- Scope: PCC metrics for tool-calling (skill/prime/agent)
- Metrics definitions (path/tool/instruction correctness, false vs safe fallback, determinism)
- Data sources (dataset + eval-plan output + PRIME feature_map)
- Guardrails (tie->fallback, true_zero_guidance=0)

**Step 2: Commit**

```bash
git add docs/adr/ADR_PCC_METRICS.md
git commit -m "docs: add PCC metrics ADR"
```

---

### Task 5: Full test sweep

**Step 1: Run tests**

```bash
uv run pytest
```
Expected: PASS.

---

Plan complete and saved to `docs/plans/2025-12-31-pcc-metrics-plan.md`. Two execution options:

1. Subagent-Driven (this session) — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) — Open new session with executing-plans, batch execution with checkpoints

Which approach?
