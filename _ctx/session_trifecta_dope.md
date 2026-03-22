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
