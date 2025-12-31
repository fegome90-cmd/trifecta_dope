# T9.2.1 Generalization Report: ctx.plan Anti-Overfitting

**Date**: 2025-12-31
**Mode**: Evidence-Only + No-Gaming + Fail-Closed
**Decision**: ❌ **NO-GO**

---

## Executive Summary

| Dataset | Plan Hit Rate | Plan Miss Rate | Zero Hit Rate | Gate |
|---------|--------------|----------------|---------------|------|
| v1 (trifecta_dope) | 85.0% (17/20) | 15.0% (3/20) | 0% | ✅ GO |
| v2 (trifecta_dope) | 60.0% (24/40) | 40.0% (16/40) | 0% | ❌ NO-GO |
| v2 (AST) | 0.0% (0/40) | 100.0% (40/40) | 0% | ❌ NO-GO |

**Conclusion**: The v1 results were **overfitted** to specific phrasing patterns. When tested with v2 (same domain, different phrasing), plan_miss_rate increased from 15% to 40%, failing the <20% threshold.

---

## Commands Executed (Reproducible)

### 1. Dataset v2 Creation
```bash
# Created: docs/plans/t9_plan_eval_tasks_v2.md
# 40 tasks: 20 new, 10 ambiguous, 10 edge cases
# Task IDs: T9V2-001 to T9V2-040
```

### 2. Evaluation v2 on trifecta_dope
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2.md
```

**Output**:
```
============================================================
EVALUATION REPORT: ctx.plan
============================================================
Dataset: docs/plans/t9_plan_eval_tasks_v2.md
Segment: .
Total tasks: 40

Results:
  Plan hits:   24 (60.0%)
  Plan misses: 16 (40.0%)

Selection Method Distribution:
  feature: 0 (0.0%)
  alias: 24 (60.0%)
  fallback: 0 (0.0%)

Top Missed Tasks:
  1. can you show me the token counting logic
  2. explain how primes organize the reading list
  3. walk through the chunk retrieval flow
  4. locate the GetChunkUseCase implementation
  5. where is the event flush mechanism defined

Examples (task → selected_feature → returned):
  • 'where would i find stats about search performance'
    → observability_telemetry (6 chunks, 3 paths)
  • 'i need to design a ctx export feature'
    → observability_telemetry (6 chunks, 3 paths)
  • 'what does the clean architecture look like here'
    → arch_overview (4 chunks, 2 paths)

❌ NO-GO: plan_miss_rate 40.0% >= 20%
```

### 3. Evaluation v2 on Second Segment (AST)
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run trifecta ctx eval-plan -s ~/Developer/AST --dataset docs/plans/t9_plan_eval_tasks_v2.md
```

**Output**:
```
============================================================
EVALUATION REPORT: ctx.plan
============================================================
Dataset: docs/plans/t9_plan_eval_tasks_v2.md
Segment: /Users/felipe_gonzalez/Developer/AST
Total tasks: 40

Results:
  Plan hits:   0 (0.0%)
  Plan misses: 40 (100.0%)

Selection Method Distribution:
  feature: 0 (0.0%)
  alias: 0 (0.0%)
  fallback: 0 (0.0%)

❌ NO-GO: plan_miss_rate 100.0% >= 20%
```

### 4. Regression Tests
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run pytest tests/test_plan_use_case.py -v
```

**Output**:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 6 items

tests/test_plan_use_case.py::test_plan_prefers_feature_over_alias_over_fallback PASSED [ 16%]
tests/test_plan_use_case.py::test_plan_does_not_match_generic_triggers PASSED [ 33%]
tests/test_plan_use_case.py::test_plan_returns_why_selected_by PASSED [ 50%]
tests/test_plan_use_case.py::test_repo_map_generation_is_capped_and_deterministic PASSED [ 66%]
tests/test_plan_use_case.py::test_plan_fail_closed_on_invalid_feature PASSED [ 83%]
tests/test_plan_use_case.py::test_plan_high_signal_trigger_matches_single_term PASSED [100%]

============================== 6 passed in 0.05s ===============================
```

### 5. Stub Regeneration Test
```bash
uv run trifecta ctx sync -s .
```

**Output**:
```
🔄 Running build...
✅ Build complete. Validating...
✅ Validation Passed
🔄 Regenerating stubs...
   ✅ Regenerated: repo_map.md, symbols_stub.md
```

---

## v1 vs v2 Comparison Table

| Metric | v1 (20 tasks) | v2 (40 tasks) | Delta |
|--------|--------------|--------------|-------|
| Plan hits | 17 (85.0%) | 24 (60.0%) | -25% |
| Plan misses | 3 (15.0%) | 16 (40.0%) | +25% |
| Zero hits | 0 (0%) | 0 (0%) | 0% |
| selected_by="alias" | 17 (85.0%) | 24 (60.0%) | -25% |
| selected_by="feature" | 0 (0%) | 0 (0%) | 0% |
| selected_by="fallback" | 3 (15.0%) | 16 (40%) | +25% |

**Analysis**: The 25% drop in plan_hit_rate indicates that triggers were overfitted to v1 phrasing patterns.

---

## Top 10 Missed Tasks v2

| # | Task | Expected Feature | Why Missed |
|---|------|------------------|------------|
| 1 | "can you show me the token counting logic" | observability_telemetry | "token counting" != "token tracking" |
| 2 | "explain how primes organize the reading list" | context_pack | "reading list" != "build process" |
| 3 | "walk through the chunk retrieval flow" | search | "retrieval flow" != "search use case" |
| 4 | "locate the GetChunkUseCase implementation" | search | Class name missing "UseCase" suffix match |
| 5 | "where is the event flush mechanism defined" | observability_telemetry | "flush mechanism" != "method flush()" |
| 6 | "list all typer commands available" | cli_commands | "typer commands" != "cli commands" |
| 7 | "what files exist under src/domain" | code_navigation | No trigger for directory listing |
| 8 | "show me the token estimation formula" | observability_telemetry | "formula" != "function implementation" |
| 9 | "how is the Telemetry class constructed" | observability_telemetry | "constructed" != "initialization" |
| 10 | "what imports are needed" | symbol_surface | No trigger for import queries |

---

## 5 Example Traces

### Example 1: Hit with alias match
**Task**: "where would i find stats about search performance"

| Field | Value |
|-------|-------|
| selected_feature | `observability_telemetry` |
| selected_by | `alias` |
| match_terms_count | 2 |
| matched_trigger | "hit rate" (trigger phrase) |
| chunks | `["skill:*", "agent:*", "ref:RELEASE_NOTES_v1.md"]` |
| paths | `["README.md", "RELEASE_NOTES_v1.md", "src/infrastructure/telemetry.py"]` |
| why | L2: Alias match via 'hit rate' (2 terms) |

### Example 2: Hit with architecture match
**Task**: "what does the clean architecture look like here"

| Field | Value |
|-------|-------|
| selected_feature | `arch_overview` |
| selected_by | `alias` |
| match_terms_count | 2 |
| matched_trigger | "clean architecture" |
| chunks | `["prime:*", "agent:*"]` |
| paths | `["README.md", "_ctx/generated/repo_map.md"]` |
| why | L2: Alias match via 'clean architecture' (2 terms) |

### Example 3: Miss due to phrasing
**Task**: "can you show me the token counting logic"

| Field | Value |
|-------|-------|
| selected_feature | `null` |
| selected_by | `fallback` |
| match_terms_count | 0 |
| matched_trigger | `null` |
| chunks | `[]` |
| paths | `["README.md", "skill.md", ...]` (entrypoints) |
| why | L3: No feature match, using entrypoints |

**Root cause**: Trigger "token tracking" doesn't match "token counting logic"

### Example 4: Miss due to synonym
**Task**: "walk through the chunk retrieval flow"

| Field | Value |
|-------|-------|
| selected_feature | `null` |
| selected_by | `fallback` |
| match_terms_count | 0 |
| chunks | `[]` |
| paths | entrypoints |

**Root cause**: Trigger "search query" doesn't match "chunk retrieval flow"

### Example 5: Edge case hit
**Task**: "telemetry architecture overview"

| Field | Value |
|-------|-------|
| selected_feature | `arch_overview` |
| selected_by | `alias` |
| match_terms_count | 2 |
| matched_trigger | "repo architecture" (matches "architecture" + "telemetry" as generic terms) |
| chunks | `["prime:*", "agent:*"]` |
| paths | `["README.md", "_ctx/generated/repo_map.md"]` |

**Note**: This matched via "architecture" keyword, but "telemetry" was ignored. Shows multi-concept queries can match partially.

---

## Second Segment Analysis

**Segment**: `/Users/felipe_gonzalez/Developer/AST`

| Characteristic | Value |
|----------------|-------|
| Has `_ctx/` | ✅ |
| Has `prime_*.md` | ✅ (prime_ast.md) |
| Has `agent.md` | ✅ |
| Has `telemetry/` | ✅ (42 events) |
| Has `aliases.yaml` | ✅ (schema v1, not v2) |

**Result**: 100% fallback because AST uses schema v1 aliases which lack the structured triggers needed for v2 tasks.

**Finding**: The router is segment-specific. Each segment needs its own aliases.yaml tuned to its domain. Cross-segment generalization is not a goal of PCC.

---

## Regression Test Coverage

```
tests/test_plan_use_case.py coverage:

test_plan_prefers_feature_over_alias_over_fallback    PASSED
test_plan_does_not_match_generic_triggers               PASSED
test_plan_returns_why_selected_by                       PASSED
test_repo_map_generation_is_capped_and_deterministic    PASSED
test_plan_fail_closed_on_invalid_feature                PASSED
test_plan_high_signal_trigger_matches_single_term        PASSED
```

**Caveat**: Coverage tests verify behavior but don't prevent overfitting.

---

## Stub Regeneration

**Implementation**: `src/application/stub_regen_use_case.py`
**Integration**: `ctx sync` now regenerates stubs after validation

| Stub | Max Lines | Actual Lines | Status |
|------|-----------|--------------|--------|
| repo_map.md | 300 | 60 | ✅ Within cap |
| symbols_stub.md | 200 | 29 | ✅ Within cap |

**Telemetry event**: `ctx.sync.stub_regen` with `regen_ok` and `reason` fields.

---

## Root Cause Analysis

### Why v1 Passed, v2 Failed

1. **Trigger Phrasing Mismatch**
   - v1: "function _estimate_tokens implementation"
   - v2: "show me the token estimation formula"
   - Trigger: "function implementation" (matches v1, not v2)

2. **Verb/Preposition Variance**
   - v1: "where are the CLI commands defined"
   - v2: "list all typer commands available"
   - Trigger: "cli commands defined" (matches v1, not v2)

3. **Synonym Gaps**
   - "counting" vs "tracking"
   - "retrieval flow" vs "search"
   - "formula" vs "function"

4. **Overfitting to Exact Phrases**
   - Triggers were tuned based on v1 task wording
   - Same semantic meaning, different syntax → miss

---

## GO/NO-GO Decision

| Criterion | Target | v1 Result | v2 Result | Status |
|-----------|--------|-----------|-----------|--------|
| plan_miss_rate | < 20% | 15% | 40% | ❌ FAIL |
| zero_hit_rate | <= 5% | 0% | 0% | ✅ PASS |
| alias <= 70% | <= 70% | 85% | 60% | ✅ PASS |
| feature >= 10% | >= 10% | 0% | 0% | ⚠️ WARNING |
| fallback <= 20% | <= 20% | 15% | 40% | ❌ FAIL |

**Final Gate**: ❌ **NO-GO**

**Reason**: `plan_miss_rate` of 40% on v2 dataset is 2x the 20% threshold. The system is overfitted to v1 phrasing patterns.

---

## Recommendations

To achieve <20% plan_miss_rate on holdout data:

1. **Add Synonym Triggers**
   - "token counting" → observability_telemetry
   - "chunk retrieval" → search
   - "typer commands" → cli_commands
   - "formula/equation" → function implementation

2. **Normalize Verb Patterns**
   - Add triggers for: "show me", "walk through", "locate", "list"
   - Combine with domain terms

3. **Increase Fuzzy Matching**
   - Consider word stem matching (count/counting/counted)
   - Consider semantic clustering (formula/function/implementation)

4. **Add "Unknown" Feature**
   - Catch-all for domain-ambiguous queries
   - Routes to prime entrypoints with explanation

5. **Per-Segment Tuning**
   - Each segment needs domain-specific triggers
   - Cross-segment generalization is not expected in PCC model

---

## Deliverables Status

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| 1) Dataset v2 | ✅ | docs/plans/t9_plan_eval_tasks_v2.md |
| 2) Evaluation v2 | ✅ | Output above (NO-GO) |
| 3) Second segment test | ✅ | AST segment tested (100% fallback) |
| 4) Regression tests | ✅ | 6 tests PASS |
| 5) Stub regeneration | ✅ | ctx.sync regenerates deterministically |
| 6) Evidence report | ✅ | This document |

---

**Report Generated**: 2025-12-31
**Status**: ❌ NO-GO - Generalization target not met
**Next Step**: Expand triggers with synonyms OR accept 40% miss rate as baseline for PCC-only approach
