# Audit 1: MR Thorough — skill-hub-render-unification

**Date**: 2026-05-01
**Preset**: thorough (4 agents, 2 batches)
**Skill**: mr-plan v1.3
**Recommendation**: **CAUTION** — 3 HIGH findings, fix before production

---

## Summary

| Severity | Count | Confirmed (2+ agents) |
|----------|-------|----------------------|
| CRITICAL | 0 | — |
| HIGH | 3 | 2 |
| MEDIUM | 8 | 2 |
| LOW | 9 | 0 |
| **Total** | **20** | |

---

## HIGH Findings

### H-1: cli() returns 0 for rejected queries [CONFIRMED ×4]
- **Agents**: structure, risk, design, simplification (ALL FOUR)
- **Location**: `scripts/skill_hub_cards_core.py:542-549`
- **Issue**: Empty/whitespace queries caught by sanitize_query return EXIT_RENDERABLE (0) instead of EXIT_ERROR (1)
- **Impact**: CI pipelines and wrappers checking exit codes will interpret rejected input as success
- **Fix**: Return EXIT_ERROR (1) when sanitize_query raises ValueError

### H-2: output_json() exposes all RuntimeSkillCard fields [CONFIRMED ×3]
- **Agents**: risk, design, simplification
- **Location**: `scripts/skill_hub_cards_core.py:502`
- **Issue**: Uses `card.__dict__` which exposes internal fields (search_hints, triggers, compact_flag, fidelity_level) and creates implicit API contract
- **Fix**: Use explicit field allowlist for JSON serialization

### H-3: SearchRuntimeError/GetRuntimeError are identical
- **Agent**: simplification
- **Location**: `scripts/skill_hub_cards_core.py:107-118`
- **Issue**: Both classes have identical structure, constructor, and handling
- **Fix**: Collapse into single SubprocessRuntimeError with source field

---

## MEDIUM Findings

| # | Category | Finding | Agents |
|---|----------|---------|--------|
| M-1 | coupling | SkillCardViewModel import in cards_core unnecessary | 3 |
| M-2 | security | Bash temp files use predictable PID names | 1 |
| M-3 | observability | Captured stderr silently discarded | 1 |
| M-4 | type-safety | authority_state typed as str, not Literal | 2 |
| M-5 | duplication | run_search/run_get duplicate timeout logic (~40 lines) | 1 |
| M-6 | type-safety | build_view_model() missing return type annotation | 1 |
| M-7 | api-design | SkillCard factory shadows class name | 1 |
| M-8 | redundancy | _validate_positive_limit duplicates argparse validation | 1 |

---

## Execution Metadata

| Agent | Findings | Confidence | Duration |
|-------|----------|------------|----------|
| structure | 12 (0/0/3/9) + 6 PASS | 0.92 | ~2m |
| risk | 8 (0/1/3/4) | 0.92 | ~3m |
| design | 11 (0/2/7/2) | 0.88 | ~2m |
| simplification | 11 (0/2/5/4) | 0.88 | ~2m |

**Quorum**: 4/4 agents (100%)

---

## Recommended Actions

1. **Fix H-1** (exit code) — 1 line change + 2 tests
2. **Fix H-2** (output_json allowlist) — Add to_dict() or field filter
3. **Fix H-3** (collapse error classes) — Replace with single class + source field
