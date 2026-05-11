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

## 2026-05-09 Git Hygiene Phase 5 Cleanup
- **Summary**: SDD git-hygiene-phase5-cleanup — 6 cleanup actions, 32 tasks across 7 phases. Full SDD cycle (explore→verify). Committed `e6e115d0` on main.
- **Actions**: Deleted dead `.git/hooks/pre-commit`, removed worktree + 2 local branches, closed PR #85, created 10 GitHub labels + assigned 6 issues (#87-#92), removed plotly ghost dep from pyproject.toml, updated tree-sitter floors to >=0.25.2/>=0.25.0, deleted 11+1 remote branches
- **Post-audit corrections**: Added missing `good first issue` label to #90, ran `git fetch --prune` to clean stale remote tracking ref
- **Verification**: 6/6 spec requirements COMPLIANT, 8/8 design decisions followed, PASS
- **Engram artifacts**: #2727 (explore), #2730 (proposal), #2732 (design), #2733 (spec), #2734 (tasks), #2735 (gate), #2736 (apply-progress), #2738 (verify-report)
- **Commit**: `e6e115d0` chore: remove plotly ghost dep, update tree-sitter floors
- **Next**: sdd-archive

## 2026-05-09 Git Hygiene Phase 5+6 Closeout + Archive + Follow-ups
- **Summary**: Completed Phase 6 (document authority fix), archived SDD change, executed follow-up #1 (closed-pr semantic memo)
- **Phase 6** (`f50bc595`): Created authority registry, inserted STATUS headers in 3 docs, corrected phase-2-closeout PRESERVED/DELETED counts
- **Archive**: SDD change archived in engram #2747. Follow-ups registered: #2748 (dependabot policy), #2749 (stash retention), #2750 (closed-pr memo)
- **Anchor docs** (`e2627999`, `5a201707`): Cherry-picked hygiene/ from remote branch, updated with Phase 4+5 resolution, anchored to main
- **Closed-PR semantic memo** (`c6ea4112`): Documented PRESERVED vs DELETED rationale for 6 closed-PR branches. Authority registry updated.
- **Commits**: `e2627999`, `3b9f13dd`, `5a201707`, `f50bc595`, `c6ea4112`
- **Remaining follow-ups**: stash-retention-policy (#2749), dependabot-policy (#2748)
- **Next**: stash-retention-policy or close session

## 2026-05-09 Closed-PR Semantic Memo Correction
- **Summary**: Micro-corrección documental al closed-pr semantic memo. No operational changes.
- **Changes**: Added evidence strength column (HIGH/MEDIUM-LOW/LOW-MEDIUM), adjusted Rule 5 for honesty, added accepted residual risk section, clarified patch status in phase-6 report, added duplicate warning to README, created correction report.
- **Commits**: `22f7158a` docs: clarify closed-pr semantic risk levels and residual uncertainty
- **Next**: stash-retention-policy (#2749)

## 2026-05-09 Stash Retention Policy Draft
- **Summary**: Audited `origin/hygiene/stash-preserve-codex-freeze` (310 files, 188,689 insertions, 132,771 deletions, commit `07a8cf4d`), evaluated 4 retention options, drafted policy. No operational changes.
- **Findings**: 310 files across 30+ top-level dirs. 5 files >1MB (largest: 87.3MB reconcile.patch). No actual secrets found (only audit reports about secrets/tokens). Content is superset of old stash/codex freeze. Categories: ~197 .md docs, ~55 .py files, ~38 config/data files.
- **Recommendation**: Option B — create annotated tag `stash-preserve-codex-freeze-v1` + maintain branch. Zero data loss risk, minimal cost, discoverable by agents.
- **Commits**: `6d47e3c4` docs: draft stash retention policy for hygiene/stash-preserve-codex-freeze
- **Next**: Human review → approve tag creation → update policy status to APPROVED → mark follow-up COMPLETE.

## 2026-05-09 Stash Retention Policy Implemented
- **Summary**: Executed Option B — created annotated tag `stash-preserve-codex-freeze-v1` pointing to same commit as branch. Branch maintained. No operational deletions.
- **Tag**: stash-preserve-codex-freeze-v1 → 07a8cf4d1527148ef2910ae69277c049e40f4179
- **Branch**: origin/hygiene/stash-preserve-codex-freeze → 07a8cf4d1527148ef2910ae69277c049e40f4179
- **Verification**: Both resolve to same commit ✅
- **Commits**: `c6c55cb9` docs: implement stash retention policy with annotated tag
- **Next**: dependabot-policy (#2748)

## 2026-05-09 Stash Retention Policy Correction
- **Summary**: Micro-corrección documental: replaced "zero risk" with "low risk, not zero", corrected "sole preservation" to acknowledge tag as additional reference, clarified commit provenance (README had `03eede58`, corrected to `c6c55cb9`).
- **Commits**: `0b8a64db` docs: clarify stash retention residual risk and commit provenance
- **Next**: dependabot-policy (#2748)
