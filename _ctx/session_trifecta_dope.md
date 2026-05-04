# session.md - Trifecta Context Runbook

segment: trifecta_dope

## Purpose
This file is a **runbook** for using Trifecta Context tools efficiently:
- progressive disclosure (search -> get)
- strict budget/backpressure
- evidence cited by [chunk_id]

## Quick Commands (CLI)
```bash
# SEGMENT="." es valido SOLO si tu cwd es el repo target (el segmento).
# Si ejecutas trifecta desde otro lugar (p.ej. desde el repo del CLI), usa un path absoluto:
# SEGMENT="/abs/path/to/AST"
SEGMENT="."

# Usa un termino que exista en el segmento (ej: nombre de archivo, clase, funcion).
# Si no hay hits, refina el query o busca por simbolos.
trifecta ctx sync --segment "$SEGMENT"
trifecta ctx search --segment "$SEGMENT" --query "<query>" --limit 6
trifecta ctx get --segment "$SEGMENT" --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
trifecta ctx validate --segment "$SEGMENT"
trifecta load --segment "$SEGMENT" --mode fullfiles --task "Explain how symbols are extracted"
```

## Rules (must follow)

* Max **1 ctx.search + 1 ctx.get** per user turn.
* Prefer **mode=excerpt**; use raw only if necessary and within budget.
* Cite evidence using **[chunk_id]**.
* If **validate fails**: stop, rebuild. **No silent fallback**.
* **STALE FAIL-CLOSED**: If `stale_detected=true`, STOP -> `ctx sync` + `ctx validate` -> log "Stale: true -> sync+validate executed" -> continue only if PASS.

## Session Log (append-only)

### Entry Template (max 12 lines)
```md
## YYYY-MM-DD HH:MM - ctx cycle
- Segment: .
- Objective: <que necesitas resolver>
- Plan: ctx sync -> ctx search -> ctx get (excerpt, budget=900)
- Commands: (pending/executed)
- Evidence: (pending/[chunk_id] list)
- Warnings: (none/<code>)
- Next: <1 concrete step>
```

Reglas:
- **append-only** (no reescribir entradas previas)
- una entrada por run
- no mas de 12 lineas

## TRIFECTA_SESSION_CONTRACT (NON-EXECUTABLE in v1)

> Documentation only. Not executed automatically in v1.

```yaml
schema_version: 1
segment: .
autopilot:
  enabled: false
  note: "v2 idea only - NOT executed in v1"
```

## Watcher Example (optional)

```bash
# Ignore _ctx to avoid loops.
fswatch -o -e "_ctx/.*" -i "skill.md|prime.md|agent.md|session.md" . \
  | while read; do trifecta ctx sync --segment "$SEGMENT"; done
```

## Next User Request

<!-- The next agent starts here -->

## 2026-03-15 01:56 UTC
- **Summary**: Review graph branch changes in isolated worktree
- **Files**: src/application/graph_indexer.py, docs/contracts/GRAPH_MVP.md, tests/unit/test_graph_indexer.py, tests/unit/test_graph_service.py, tests/integration/cli/test_graph_cli.py, tests/unit/test_graph_contract_boundaries.py
- **Commands**: git diff, pytest
- **Pack SHA**: `24aafcfcd3c77523`

## 2026-03-15 16:22 UTC
- **Summary**: Fix skill-hub --help flag handler
- **Problem**: `skill-hub --help` searched for "--help" string instead of showing usage
- **Solution**: Add explicit --help/-h handler before query processing
- **Files**: ~/.local/bin/skill-hub → scripts/skill-hub (versioned)
- **Commit**: `c43e6d7` feat(skill-hub): add --help/-h flag handler
- **Validation**: Tested --help, -h, empty args, and normal search
- **Pack SHA**: `c43e6d7780c2a583`

## 2026-03-13 17:49 UTC
- **Summary**: Implemented Graph MVP: new graph CLI namespace, SQLite store keyed by SegmentRef V1 id, AST top-level indexing for src/**/*.py, conservative direct-call edges, search/status/callers/callees, focused tests and manual CLI verification
- **Files**: src/domain/graph_models.py, src/infrastructure/graph_store.py, src/application/graph_indexer.py, src/application/graph_service.py, src/infrastructure/cli_graph.py, src/infrastructure/cli.py, tests/integration/test_graph_store_schema.py, tests/unit/test_graph_indexer.py, tests/unit/test_graph_service.py, tests/integration/cli/test_graph_cli.py, docs/plans/2026-03-13-graph-mvp-implementation-plan.md
- **Commands**: make install, uv run pytest, uv run ruff check, uv run trifecta graph
- **Pack SHA**: `fac5ddcf14590d10`

## 2026-03-14 00:12 UTC
- **Summary**: Fixed first Graph MVP review batch: status no longer creates DBs on pristine segments, nested calls no longer leak into top-level edges, and callers/callees now fail closed on ambiguous symbols with structured CLI errors.
- **Files**: src/application/graph_indexer.py, src/application/graph_service.py, src/infrastructure/graph_store.py, src/infrastructure/cli_graph.py, tests/unit/test_graph_indexer.py, tests/unit/test_graph_service.py, tests/integration/cli/test_graph_cli.py, docs/plans/2026-03-13-graph-mvp-review-fixes-plan.md, _ctx/session_trifecta_dope.md
- **Commands**: uv run pytest, uv run ruff check, uv run mypy
- **Pack SHA**: (unchanged)

## 2026-03-15 11:47 UTC
- **Summary**: Resume graph review-fix batch in codex/graph-mvp; inspect Graph store/service/indexer and add TDD regressions for the 5 pending PR #74 findings
- **Files**: src/infrastructure/graph_store.py, src/application/graph_service.py, src/application/graph_indexer.py, tests/integration/cli/test_graph_cli.py, tests/unit/test_graph_service.py, tests/unit/test_graph_indexer.py
- **Commands**: make install, sed, rg, pytest, ruff
- **Pack SHA**: `005855ec718feceb`

## 2026-03-15 11:52 UTC
- **Summary**: Completed Graph review-fix batch: relation queries now stay on calls edges and segment scope, injected-store reads preserve pristine semantics, and indexer covers direct constructor calls without leaking nested call arguments. Verified targeted Graph pytest slice and Ruff.
- **Files**: src/application/graph_indexer.py, src/application/graph_service.py, src/infrastructure/graph_store.py, tests/integration/test_graph_store_schema.py, tests/unit/test_graph_indexer.py, tests/unit/test_graph_service.py
- **Commands**: uv run pytest -q tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py, uv run ruff check src/application/graph_indexer.py src/application/graph_service.py src/infrastructure/graph_store.py tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py
- **Pack SHA**: `005855ec718feceb`

## 2026-03-15 12:15 UTC
- **Summary**: Tightened GraphService injected-store matching: neighbor DBs in the same cache dir are no longer reused when the canonical segment DB exists. Added regression coverage and reverified the focused Graph slice.
- **Files**: src/application/graph_service.py, tests/unit/test_graph_service.py
- **Commands**: uv run pytest -q tests/unit/test_graph_service.py -k neighbor_injected_store, uv run pytest -q tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py, uv run ruff check src/application/graph_indexer.py src/application/graph_service.py src/infrastructure/graph_store.py tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py
- **Pack SHA**: `005855ec718feceb`

## 2026-03-15 12:28 UTC
- **Summary**: Closed final pre-commit Graph warning: GraphService now canonicalizes injected-store path comparisons so alias/symlink paths still match the intended segment cache. Added regression coverage and reverified the Graph slice.
- **Files**: src/application/graph_service.py, tests/unit/test_graph_service.py
- **Commands**: uv run pytest -q tests/unit/test_graph_service.py -k alias_path_for_injected_store, uv run pytest -q tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py, uv run ruff check src/application/graph_indexer.py src/application/graph_service.py src/infrastructure/graph_store.py tests/integration/test_graph_store_schema.py tests/unit/test_graph_indexer.py tests/unit/test_graph_service.py tests/integration/cli/test_graph_cli.py
- **Pack SHA**: `005855ec718feceb`

## 2026-04-29 UTC
- **Summary**: Full dry-run audit of skill-hub search/cards/runtime after reported regressions.
- **Findings**: Runtime receipt verifies and promoted files match repo; sandbox blocks uv cache; manifest has 489 entries with 0 orphans/dups/truncated descriptions; audit still reports 12 broken registered source paths and coverage gap.
- **Findings**: Search is degraded by vague-query expansion adding `agent.md prime.md`, causing code-review/pae-agent noise; wrapper canonical alias logic still assumes `repo:{term}.md:` while live ids are `skill:{name}:{hash}`.
- **Findings**: Cards render outside sandbox, but intro/banner contract is broken; focused tests show runtime-promotion failures and render parity tests fail collection due stale `SkillCardViewModel` API expectations.
- **Commands**: skill-hub smoke, uv run trifecta ctx search --explain, audit_skill_hub.py --report-out, pytest focused skill-hub card/runtime slices.
- **Files**: scripts/skill-hub, scripts/skill_hub_cards_core.py, scripts/skill-hub-runtime, tests/unit/test_skill_hub_runtime_promotion.py, tests/unit/test_skill_hub_render_parity.py, _ctx/session_trifecta_dope.md

## 2026-04-29 UTC
- **Summary**: Started SDD cycle `skill-hub-surgical-repair` with explore phase.
- **Artifact**: openspec/changes/skill-hub-surgical-repair/exploration.md
- **Findings**: Five drifts confirmed: legacy-only alias refs, skills-hub-inappropriate vague query anchors, split cards authority, intro/banner contract drift, and governed-only registration repair requirement.
- **Decision**: Use surgical governed-runtime repair; no rebuild masivo and no manual manifest/receipt edits.
- **Next**: Run sdd-propose/spec/design for the same change before apply.

## 2026-04-30 UTC
- **Summary**: Fixed recurring `skill-hub --cards` rich render regression by changing the wrapper to use the project Python/uv environment before falling back to system `python3`.
- **Findings**: Root cause was Python interpreter dependency drift: system `python3` lacked `rich`, so `render_cards_rich()` silently fell back to plain even though `uv run python` had `rich`.
- **Commands**: uv run pytest focused skill-hub runtime/card suites; scripts/skill-hub-runtime promote; scripts/skill-hub-runtime verify; skill-hub --cards python --limit 1 in TTY and non-TTY.
- **Files**: scripts/skill-hub, tests/unit/test_skill_hub_runtime_promotion.py, ~/.codex/skills/skill-hub-doctor/resources/diagnostic-checks.md, ~/.codex/skills/skill-hub-doctor/resources/known-failures.md, ~/.codex/skills/skill-hub-doctor/resources/repair-procedures.md, _ctx/session_trifecta_dope.md

## 2026-04-30 UTC
- **Summary**: Fixed missing `skill-hub --cards` intro/banner handoff after rich cards were restored.
- **Findings**: Root cause was an integration gap: `scripts/skill_hub_runtime_ux.py::render_intro()` was correct, but `scripts/skill_hub_cards_core.py::cli()` printed rendered cards directly and never called the governed intro renderer.
- **Fix**: Cards CLI now computes `is_tty` once, passes it to `_select_renderer(...)`, and prepends `render_intro(query_hint=args.query, rich=is_tty and args.style == "rich")` for non-JSON renderable card output only.
- **Commands**: uv run pytest focused skill-hub suite (48 passed); scripts/skill-hub --cards python --limit 1 non-TTY + TTY; scripts/skill-hub-runtime promote; scripts/skill-hub-runtime verify; skill-hub --cards python --limit 1 non-TTY + TTY.
- **Files**: scripts/skill_hub_cards_core.py, tests/unit/test_skill_hub_cards_adapter.py, ~/.codex/skills/skill-hub-doctor/resources/diagnostic-checks.md, ~/.codex/skills/skill-hub-doctor/resources/known-failures.md, ~/.codex/skills/skill-hub-doctor/resources/repair-procedures.md, _ctx/session_trifecta_dope.md

## 2026-04-30 UTC
- **Summary**: Closed four real HIGH findings from the parallel skill-hub hunt and rejected the null-byte finding as an argv-layer false HIGH.
- **Findings**: H-001/H-002 shared a root cause: managed skill excerpts start with indexing scaffolding (`<!-- managed-by... -->`, `read ...`, `# Skill`, `**Source**`) and the renderers were using raw preview/too-narrow description patterns instead of extracting the first human content line.
- **Findings**: H-003 cannot be fixed inside skill-hub because NUL bytes cannot survive `argv`; `python3 -c 'print(repr(sys.argv[1]), len(sys.argv[1]))' $'test\x00null'` receives only `'test'` length 4 before skill-hub runs.
- **Fix**: Plain search preview now hides managed scaffolding; cards promote generic managed descriptions to healthy/full cards; cards whitespace-only queries now reject before search with the same message as plain mode; no-args wrapper now prints full help including `--cards` and `--limit`.
- **Commands**: uv run pytest focused skill-hub render/runtime suite (52 passed); bash scripts/skill-hub security; bash scripts/skill-hub --cards testing --limit 3; bash scripts/skill-hub --cards '   '; bash scripts/skill-hub; scripts/skill-hub-runtime promote; scripts/skill-hub-runtime verify; promoted `skill-hub` smokes for preview/cards/whitespace/no-args/TTY.
- **Files**: src/application/search_get_usecases.py, scripts/skill_hub_cards_core.py, scripts/skill-hub, tests/unit/test_skill_hub_search_render_surface.py, tests/unit/test_skill_hub_cards_adapter.py, tests/unit/test_skill_hub_runtime_promotion.py, _ctx/session_trifecta_dope.md

## 2026-05-01 UTC
- **Summary**: Fixed skill-hub plain search path discoverability after the default render stopped exposing usable skill source paths.
- **Findings**: `skill-hub --cards "skill-hub doctor"` already showed `read /.../SKILL.md`; the broken surface was plain `skill-hub`/`trifecta ctx search`, where `read ...` was filtered from previews and truncated index previews could show `**Resolved Path**` instead of a useful description.
- **Fix**: Plain search now loads full skill chunks for display, emits a dedicated `Path: .../SKILL.md` line for `skill:` hits, and still uses a human-readable preview with managed scaffolding hidden.
- **Commands**: `.venv/bin/pytest tests/unit/test_skill_hub_search_render_surface.py tests/unit/test_skill_hub_cards_adapter.py::test_cli_cards_output_includes_plain_intro_before_rendered_cards -q`; `.venv/bin/trifecta ctx search --segment ~/.trifecta/segments/skills-hub --query "skill-hub doctor" --limit 1`; `~/.local/bin/skill-hub "skill-hub doctor" --limit 1`; `~/.local/bin/skill-hub --cards "skill-hub doctor" --limit 1`.
- **Files**: src/application/search_get_usecases.py, tests/unit/test_skill_hub_search_render_surface.py, _ctx/session_trifecta_dope.md

## 2026-05-01 UTC
- **Summary**: Validated the proposed 8 HIGH findings for `skill-hub-render-unification` using Engram context plus code/runtime evidence.
- **Findings**: H-1, H-2, H-4, and H-5 are confirmed as real issues. H-3 is duplicated code but not HIGH by itself. H-6 is not a real CLI NUL-byte bug because argv cannot carry NUL; direct API sanitization does strip it silently. H-7 is not independent; it is H-1 plus promoted-wrapper drift. H-8 is confirmed behavior but MEDIUM because degraded/minimal metadata distinguishes it.
- **Commands**: Engram lookup for audit #2618; `nl`/`grep` over `scripts/skill_hub_cards_core.py` and `scripts/skill-hub`; direct `.venv/bin/python` reproduction for H-1/H-2/H-3/H-5/H-6/H-8; real `~/.local/bin/skill-hub --cards --json test --limit 1`; real `~/.local/bin/skill-hub --cards --style rich test --limit 1`; whitespace and argv-NUL probes.
- **Files**: scripts/skill_hub_cards_core.py, scripts/skill-hub, _ctx/session_trifecta_dope.md

## 2026-05-01 UTC
- **Summary**: Reviewed agent verification for `skill-hub-render-hardening-followup`.
- **Findings**: Source tests match the report (`73 passed`), and source behavior fixes H-1/H-2/H-5/H-8 plus wrapper flag forwarding. However, promoted runtime artifacts are stale: `scripts/skill-hub-runtime verify` fails with `source hash mismatch for skill-hub`; direct `~/.local/bin/skill-hub-cards "   " --limit 1` still exits 0, and `~/.local/bin/skill-hub --cards test --limit 101` still succeeds.
- **Verdict**: Source tree is PASS WITH WARNINGS; end-user runtime is NOT PASS until promotion/verification is completed.
- **Commands**: `.venv/bin/pytest tests/unit/test_skill_hub_render_unification.py tests/unit/test_skill_hub_cards_adapter.py -q`; `scripts/skill-hub-runtime verify`; source vs promoted runtime smokes for `--json`, whitespace, and `--limit 101`.
- **Files**: scripts/skill_hub_cards_core.py, scripts/skill-hub, scripts/skill-hub-runtime, tests/unit/test_skill_hub_render_unification.py, _ctx/session_trifecta_dope.md

## 2026-05-01 UTC
- **Summary**: Re-reviewed `skill-hub-render-hardening-followup` v2 after runtime promotion and P2 test fixes.
- **Findings**: Previous P1 runtime drift is resolved: `scripts/skill-hub-runtime verify` now passes. Promoted runtime smokes pass: whitespace query exits 4, `--limit 101` exits 1, `--json` emits whitelisted JSON fields only, and missing `--style` exits 2. P2 tests were also corrected: wrapper JSON now asserts returncode before parsing, and all-synthetic coverage now calls `build_render_plan()` with a fake ref and empty `chunk_texts`.
- **Verdict**: PASS for source tree + promoted runtime. No build was run.
- **Commands**: `scripts/skill-hub-runtime verify`; `.venv/bin/pytest tests/unit/test_skill_hub_render_unification.py tests/unit/test_skill_hub_cards_adapter.py -q`; promoted runtime smokes for whitespace, `--limit 101`, `--json`, missing `--style`, and direct helper limit cap.
- **Files**: tests/unit/test_skill_hub_render_unification.py, scripts/skill-hub, scripts/skill_hub_cards_core.py, scripts/skill_hub_runtime_ux.py, _ctx/session_trifecta_dope.md
