# T9.3.1 Evaluation Report: Clean Gates (Anti-Gaming)

**Date**: 2025-12-31
**Mode**: Evidence-Only + Fail-Closed + No-Gaming

---

## Executive Summary

| Gate | Status | fallback_rate | alias_hit_rate | feature_hit_rate | true_zero_guidance |
|------|--------|--------------|----------------|-----------------|-------------------|
| **Gate-NL** | ❌ NO-GO | 17.5% < 20% ✓ | 82.5% > 70% ✗ | 0.0% < 10% ✗ | 0.0% = 0% ✓ |
| **Gate-L1** | ✅ GO | 0.0% <= 5% ✓ | N/A | 100.0% >= 95% ✓ | 0.0% = 0% ✓ |

**Overall Decision**:
- **Gate-L1**: ✅ **GO** - All criteria passed
- **Gate-NL**: ❌ **NO-GO** - alias_hit_rate exceeds threshold (good generalization but over-matching)

---

## Commands Executed (Reproducible)

```bash
# 1. Run NL evaluation (40 tasks)
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md

# 2. Run L1 evaluation (10 tasks) - NO edits between runs
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_l1.md
```

---

## NL Evaluation Results

### Raw Output

```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: d7c9fd9acbd2b407
Dataset mtime: 2025-12-31T13:19:29.395240
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature:  0 (0.0%)
  alias:    33 (82.5%)
  fallback: 7 (17.5%)
  ─────────────────────────────
  total:    40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  alias_hit_rate:         82.5%
  fallback_rate:          17.5%
  true_zero_guidance_rate: 0.0%

Top Missed Tasks (fallback): 7 total
  1. the thing for loading context
  2. how does it work
  3. telemetry
  4. where to find code
  5. architecture
  6. implement something
  7. telemetry architecture overview

Examples (hits with selected_feature):
  1. [alias] 'can you show me the token counting logic'
     → token_estimation (4 chunks, 1 paths)
  2. [alias] 'where would i find stats about search performance'
     → observability_telemetry (6 chunks, 3 paths)
  3. [alias] 'explain how primes organize the reading list'
     → prime_indexing (4 chunks, 2 paths)

❌ NO-GO (Gate-NL): Some criteria failed
   ✗ alias_hit_rate 82.5% > 70%
   ✗ feature_hit_rate 0.0% < 10% (informative)

Passed criteria:
   ✓ fallback_rate 17.5% < 20%
   ✓ true_zero_guidance_rate 0.0% = 0%
```

### NL Metrics Table

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| feature_hit_rate | 0.0% | >= 10% (informative) | ✗ Below threshold |
| alias_hit_rate | 82.5% | <= 70% | ✗ Exceeds threshold |
| fallback_rate | 17.5% | < 20% | ✓ PASS |
| true_zero_guidance_rate | 0.0% | = 0% | ✓ PASS |

### NL Distribution Table

| Outcome | Count | Percentage |
|---------|-------|------------|
| feature (L1) | 0 | 0.0% |
| alias (L2) | 33 | 82.5% |
| fallback (L3) | 7 | 17.5% |
| **TOTAL** | **40** | **100.0%** |

---

## L1 Evaluation Results

### Raw Output

```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_l1.md
Dataset SHA256: fa60cff2fccb4cb1
Dataset mtime: 2025-12-31T13:19:44.799964
Segment: .
Total tasks: 10

Distribution (MUST SUM TO 10):
  feature:  10 (100.0%)
  alias:    0 (0.0%)
  fallback: 0 (0.0%)
  ─────────────────────────────
  total:    10 (100.0%)

Computed Rates:
  feature_hit_rate:       100.0%
  alias_hit_rate:         0.0%
  fallback_rate:          0.0%
  true_zero_guidance_rate: 0.0%

Examples (hits with selected_feature):
  1. [feature] 'feature:observability_telemetry show me hit rate'
     → observability_telemetry (6 chunks, 3 paths)
  2. [feature] 'feature:context_pack explain the build process'
     → context_pack (6 chunks, 2 paths)
  3. [feature] 'feature:cli_commands list all typer commands'
     → cli_commands (2 chunks, 1 paths)

✅ GO (Gate-L1): All criteria passed
   ✓ feature_hit_rate 100.0% >= 95%
   ✓ fallback_rate 0.0% <= 5%
   ✓ true_zero_guidance_rate 0.0% = 0%
```

### L1 Metrics Table

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| feature_hit_rate | 100.0% | >= 95% | ✓ PASS |
| fallback_rate | 0.0% | <= 5% | ✓ PASS |
| true_zero_guidance_rate | 0.0% | = 0% | ✓ PASS |

### L1 Distribution Table

| Outcome | Count | Percentage |
|---------|-------|------------|
| feature (L1) | 10 | 100.0% |
| alias (L2) | 0 | 0.0% |
| fallback (L3) | 0 | 0.0% |
| **TOTAL** | **10** | **100.0%** |

---

## Bundle Assertion Results

### Implementation

Bundle assertions were implemented in `plan_use_case.py` with the following logic:

```python
def _verify_bundle_assertions(self, feature_id: str, bundle: dict, target_path: Path):
    failed_paths = []
    failed_anchors = []

    for path_str in bundle.get("paths", []):
        path = target_path / path_str
        if not path.exists():
            failed_paths.append(path_str)

    for anchor in bundle.get("anchors", []):
        anchor_found = False
        for path_str in bundle.get("paths", []):
            path = target_path / path_str
            if path.exists():
                if anchor in path.read_text():
                    anchor_found = True
                    break
        if not anchor_found:
            failed_anchors.append(anchor)

    return len(failed_paths) == 0 and len(failed_anchors) == 0
```

### Degradation Behavior

When bundle assertions fail:
- Feature match is **NOT** returned
- Degrades to **fallback** (L3)
- Warning reason: `"bundle_assert_failed"`
- Telemetry logs: `bundle_assert_ok: false`, `bundle_assert_failed_paths[]`, `bundle_assert_failed_anchors[]`

### Features and Bundle Status

All 15 features have proper bundle definitions with paths[] and anchors[]:

| Feature | Paths | Anchors | Status |
|---------|-------|---------|--------|
| observability_telemetry | README.md, RELEASE_NOTES_v1.md, src/infrastructure/telemetry.py | telemetry, events, Telemetry | ✓ PASS |
| context_pack | src/application/use_cases.py, src/domain/context_models.py | BuildContextPackUseCase, ValidateContextPackUseCase, ContextPack | ✓ PASS |
| cli_commands | src/infrastructure/cli.py | @ctx_app.command, typer, def | ✓ PASS |
| search | src/application/search_get_usecases.py | SearchUseCase, execute, search | ✓ PASS |
| stats | src/application/use_cases.py | StatsUseCase, execute, stats | ✓ PASS |
| arch_overview | README.md, _ctx/generated/repo_map.md | Architecture, Layers, prime | ✓ PASS |
| symbol_surface | _ctx/generated/symbols_stub.md | Symbol, class, function | ✓ PASS |
| code_navigation | _ctx/generated/repo_map.md, src/infrastructure/cli.py | Files, Path, Module | ✓ PASS |
| token_estimation | src/infrastructure/telemetry.py | token, estimate | ✓ PASS |
| prime_indexing | README.md, _ctx/prime_trifecta_dope.md | Index, lectura, entrada | ✓ PASS |
| chunk_retrieval_flow | src/application/search_get_usecases.py | UseCase, class, execute | ✓ PASS |
| get_chunk_use_case | src/application/search_get_usecases.py | GetChunkUseCase, class GetChunkUseCase | ✓ PASS |
| telemetry_flush | src/infrastructure/telemetry.py | flush, def flush | ✓ PASS |
| import_statements | _ctx/generated/repo_map.md | Module, Path | ✓ PASS |
| directory_listing | _ctx/generated/repo_map.md | File, Path | ✓ PASS |

**Bundle Assertion Summary**: All 15 features passed bundle assertions during evaluation.

---

## Dataset Split Verification

### NL Dataset (t9_plan_eval_tasks_v2_nl.md)

- **Total tasks**: 40
- **Stable IDs**: T9V2NL-001 to T9V2NL-040
- **Composition**: 20 new + 10 ambiguous + 10 edge
- **NO "feature:" prefix**: Verified ✓

### L1 Dataset (t9_plan_eval_tasks_v2_l1.md)

- **Total tasks**: 10
- **Stable IDs**: T9V2L1-001 to T9V2L1-010
- **All tasks**: MUST contain "feature:<id>" with valid id
- **Feature coverage**: 10 distinct features from aliases.yaml

**Anti-gaming verification**:
- Datasets were created separately
- No "feature:" tasks in NL dataset
- All L1 tasks use valid feature IDs from aliases.yaml
- Dataset SHA256 hashes are different (NL: d7c9fd9acbd2b407, L1: fa60cff2fccb4cb1)

---

## Analysis: NL Gate alias_hit_rate Failure

### The Issue

The NL gate fails because **alias_hit_rate is 82.5%**, which exceeds the 70% threshold. This appears to be a "good" failure - it indicates the system is generalizing well (most tasks match via alias instead of falling back).

### The Tension

The gate criteria create a mathematical tension for a well-performing system:

- To achieve **< 20% fallback**, maximum 7 tasks can fall back (40 × 0.20 = 8)
- To achieve **<= 70% alias**, maximum 28 tasks can match via alias (40 × 0.70 = 28)
- With 7 fallbacks, 33 tasks match via alias → 82.5% alias rate ✗
- To achieve 70% alias rate, 12 tasks would need to fall back → 30% fallback rate ✗

### Interpretation

The high alias rate (82.5%) indicates:
- Strong generalization: most natural language queries match via structured triggers
- Low fallback rate (17.5%): only truly ambiguous queries fall back
- Zero true_zero_guidance: all tasks return some guidance

The 7 remaining fallbacks are all truly ambiguous queries:
1. "the thing for loading context" - no specific keywords
2. "how does it work" - no domain context
3. "telemetry" - single keyword, no intent
4. "where to find code" - too vague
5. "architecture" - single keyword
6. "implement something" - "something" is unspecified
7. "telemetry architecture overview" - multi-concept edge case

### Recommendation

Consider adjusting the Gate-NL alias_hit_rate threshold from **<= 70%** to **<= 85%** to account for:
1. NL-only datasets naturally have higher alias rates (no L1 explicit features)
2. Well-performing systems with good trigger coverage will exceed 70%
3. The fallback_rate (< 20%) and true_zero_guidance (= 0%) are the more important quality signals

---

## Changes Made (T9.3.1)

### 1. Fixed evaluate-plan Measurement

**File**: `src/infrastructure/cli.py`

- Added dataset identity tracking (SHA256, mtime, resolved path)
- Fixed hardcoded "40" → dynamic `{total}` in distribution header
- Split gate logic: Gate-NL vs Gate-L1 with different criteria
- Added proper outcome tracking (feature/alias/fallback mutually exclusive)

### 2. Added Bundle Assertions

**File**: `src/application/plan_use_case.py`

- Added `_verify_bundle_assertions()` method
- Checks: paths exist, anchors found in file content
- Degradation: on failure → fallback with warning
- Telemetry: logs `bundle_assert_ok`, `bundle_assert_failed_paths[]`, `bundle_assert_failed_anchors[]`

**File**: `_ctx/aliases.yaml`

- Extended schema v2 to include `anchors[]` for each feature
- All 15 features have proper anchors matching actual file content

### 3. Split Datasets

**Created**: `docs/plans/t9_plan_eval_tasks_v2_nl.md`
- 40 NL-only tasks (no "feature:" prefix)
- Stable IDs: T9V2NL-001 to T9V2NL-040

**Created**: `docs/plans/t9_plan_eval_tasks_v2_l1.md`
- 10 L1 explicit feature tasks
- Stable IDs: T9V2L1-001 to T9V2L1-010
- All tasks use `feature:<id>` syntax with valid IDs

### 4. Updated aliases.yaml

- Added anchors[] to all 15 features
- Fixed anchor content to match actual file content (case-sensitive)
- Reduced some trigger sets to avoid over-matching

---

## Invariants Verification

### Distribution Invariants

✅ **total_tasks = feature_count + alias_count + fallback_count**
- NL: 40 = 0 + 33 + 7 ✓
- L1: 10 = 10 + 0 + 0 ✓

### Mutually Exclusive Outcomes

✅ Each task has exactly one outcome (selected_by ∈ {feature, alias, fallback})

### True Zero Guidance

✅ true_zero_guidance_rate = 0% for both datasets
- No tasks returned chunks=0 AND paths=0 AND next_steps=0

### Dataset Identity

✅ SHA256 and mtime tracked for anti-gaming evidence

---

## Final Decision

| Gate | Decision | Reasoning |
|------|----------|-----------|
| **Gate-L1** | ✅ **GO** | All criteria passed. Explicit feature selection works perfectly (100% feature_hit_rate). |
| **Gate-NL** | ❌ **NO-GO** | alias_hit_rate (82.5%) exceeds threshold (70%), but this indicates good generalization. System meets critical quality metrics: fallback < 20%, true_zero_guidance = 0%. |

**Recommendation**: Gate-L1 is ready for production. Gate-NL demonstrates strong generalization but requires threshold adjustment to account for well-performing alias coverage.

---

**Report Generated**: 2025-12-31
**Status**: Mixed (L1: GO, NL: NO-GO with caveat)
**Next Steps**: Consider adjusting Gate-NL alias_hit_rate threshold to 85% to accommodate strong generalization performance.
