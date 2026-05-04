# Audit 3: Authority-Flow Audit Report

**Change**: skill-hub-render-unification
**Mode**: change-audit (delta-first)
**Skill**: authority-flow-audit v2.1
**Date**: 2026-05-01
**Status**: COMPLETE

## 1. Verdict

**HEALTHY** — The change successfully consolidates two competing renderers into a single authoritative pipeline. `runtime_ux` is now the sole rendering surface. `cards_core` delegates ALL rendering to `runtime_ux`. Factory function and import alias properly bridge to `RuntimeSkillCard` without creating divergent state. One LOW finding: deprecated shim remains alive.

## 2. Surface Inventory

| Surface | Type | Delta | Role |
|---------|------|-------|------|
| `skill_hub_cards_core.py` | Python module | [MODIFIED] | Orchestration engine. Removed render functions. Added factory, sanitize_query, authority support. |
| `skill_hub_runtime_ux.py` | Python module | [MODIFIED] | Sole rendering authority. Gained authority_state, fidelity_level, compact_flag. |
| `skill-hub` (bash) | Bash CLI | [MODIFIED] | Outer wrapper. Added run_cards_helper with Python resolution chain. |
| `skill-hub-cards` | Python script | [BASELINE] | Thin public entrypoint. Unchanged. |
| `skill_hub_cards.py` | Python script | [UNCHANGED-AFFECTED] | Deprecated shim. Delegates via os.execv. Still alive. |
| `skill_card_view_model.py` | Python module | [MODIFIED] | Import alias: `SkillCardViewModel = RuntimeSkillCard`. Was separate class. |
| `RuntimeSkillCard` | Data model | [MODIFIED] | Single authority for card data. Gained fields + __post_init__ validation. |

## 3. Authority Table

| Artifact | Authority Owner | Authority Type | Delta |
|----------|----------------|----------------|-------|
| Card data model | RuntimeSkillCard (runtime_ux) | Canonical model | [MODIFIED] |
| Card rendering (plain) | render_cards_plain (runtime_ux) | Sole renderer | [MODIFIED] |
| Card rendering (rich) | render_cards_rich (runtime_ux) | Sole renderer | [MODIFIED] |
| Search → Card pipeline | build_render_plan + build_view_model (cards_core) | Orchestration | [MODIFIED] |
| CLI entry point | cli() (cards_core) | Entry point | [MODIFIED] |
| SkillCard name | Factory function (cards_core) | Backward-compat | [NEW] |
| SkillCardViewModel name | Import alias | Backward-compat | [MODIFIED] |

## 4. Pipelines Detected

### Pipeline A: Card Rendering (governed --cards mode)
```
skill-hub --cards "query" → run_cards_helper() → exec skill-hub-cards
  → cli() → sanitize_query() → run_search() → parse_search_output()
  → build_render_plan() → classify_result() → build_view_model()
  → _select_renderer() → runtime_ux.render_cards_plain/rich()
  → stdout
```
**Active. Single rendering path. No competing renderers.**

### Pipeline B: Legacy Shim
```
skill_hub_cards.py → os.execv → skill-hub-cards → same as Pipeline A
```
**Active but deprecated. Pure delegation. No logic duplication.**

### Pipeline C: Direct Search (non-cards)
```
skill-hub "query" → run_search_capture() → raw output
```
**Active. Independent from card rendering.**

## 5. Duplications and Conflicts

| Finding | Conflict? | Evidence |
|---------|-----------|----------|
| SkillCard factory vs RuntimeSkillCard | NO — factory returns RuntimeSkillCard | direct-write, high confidence |
| SkillCardViewModel alias vs RuntimeSkillCard | NO — same object at runtime (`is` identity) | direct-write, high confidence |
| Deprecated shim vs canonical entry | NO — pure delegation via os.execv | call-chain, high confidence |
| Dead code check | CLEAN — render_plain/rich absent from cards_core | grep-confirmed |

## 6. Side Effects

| New Side Effect | Risk |
|----------------|------|
| sanitize_query() raises ValueError on empty/malicious input | LOW — strengthens validation |
| RuntimeSkillCard.__post_init__ validates fields | LOW — strengthens validation |
| Bash wrapper adds belt-and-suspenders query sanitization | LOW — no mutation |
| Intro banner printed before cards | LOW — additive output |

**Concurrent execution risks: NONE.** Pipeline is read-only (search → parse → render → stdout).

## 7-8. Proposed Entrypoints / Boundaries

| Entrypoint | Owns | Status |
|------------|------|--------|
| `skill-hub --cards` | Official card rendering (bash → Python) | ✅ Canonical |
| `skill-hub-cards` | Official Python entry | ✅ Canonical |
| `skill_hub_cards_core.cli()` | Official programmatic entry | ✅ Canonical |
| `skill_hub_cards.py` | Deprecated shim | ⚠️ Schedule removal |

## 9. Prioritized Risks

| # | Risk | Severity | Confidence | Evidence |
|---|------|----------|------------|----------|
| R1 | Deprecated shim remains as active entry point | LOW | high | call-chain |
| R2 | SkillCard factory field mapping has no drift guard | LOW | medium | inferred |
| R3 | RenderPlan boundary not enforced by module | INFO | high | direct-write |
| R4 | Dynamic _import_runtime_ux() degradation not tested | LOW | medium | call-chain |

## 10. Recommended Interventions

1. **[Optional]** Schedule removal of `skill_hub_cards.py` deprecated shim
2. **[Optional]** Add field-name drift guard test for SkillCard factory
3. **[No action needed]** Pipeline is single-source, authority clear, validation strengthened

## 11. Mandatory Checklist Summary

| # | Dimension | Status |
|---|-----------|--------|
| 1 | New writers on owned state | CLEAR |
| 2 | New entrypoints to pipelines | CLEAR |
| 3 | Evidence-as-authority risk | CLEAR |
| 4 | New side effects | CLEAR |
| 5 | Validation strength change | CLEAR — STRENGTHENED |
| 6 | Legacy path status | FLAGGED (deprecated shim alive) |
| 7 | Authority expansion | CLEAR |
| 8 | Pipeline type transition | CLEAR (competing→unified) |

## H1-H5 Heuristics

| Heuristic | Result | Evidence |
|-----------|--------|----------|
| H1: Multiple entrypoints | PASS | call-chain |
| H2: Bypass | PASS | direct-write |
| H3: Lifecycle conflict | PASS | direct-write |
| H4: Double writer | PASS | direct-write |
| H5: Evidence-as-authority | PASS | direct-write |
