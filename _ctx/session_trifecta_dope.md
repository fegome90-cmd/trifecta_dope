# session.md - Trifecta Context Runbook

segment: trifecta-dope

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

## 2025-12-29 23:44 UTC
- **Summary**: Corrected T9.A to Context Routing Accuracy (not RAG). Updated aliases for routing, created evidence reports.
- **Files**: implementation_plan.md, t9a_context_routing_accuracy.md, aliases.yaml
- **Commands**: ctx sync, ctx search, session append
- **Pack SHA**: `a38f1cacdb4f0afc`

## 2025-12-29 23:49 UTC
- **Summary**: Demonstrated Trifecta CLI usage: ctx search, ctx get, ctx stats
- **Files**: skill.md
- **Commands**: ctx search, ctx get, ctx stats
- **Pack SHA**: `557f59c5e54ff34c`

## 2025-12-29 23:54 UTC
- **Summary**: Analyzed scope deviations: T9.A corrected (PCC not RAG), identified pending tasks (trifecta load, MCP, Progressive Disclosure)
- **Files**: scope_analysis.md
- **Commands**: mini-rag query, ctx search
- **Pack SHA**: `557f59c5e54ff34c`

## 2025-12-29 23:58 UTC
- **Summary**: T9 Correction Evidence Report completed: 7/9 PASS, 1 FAIL (missing prohibition), 1 BELOW (routing 75%)
- **Files**: t9-correction-evidence.md
- **Commands**: ctx validate, ctx search, ctx get, pytest
- **Pack SHA**: `557f59c5e54ff34c`

## 2025-12-30 00:12 UTC
- **Summary**: Updated prime docs (Paths), agent SOT (Tech Stack/Gates), and synced context pack.
- **Files**: _ctx/prime_trifecta_dope.md, _ctx/agent.md, _ctx/session_trifecta_dope.md, readme_tf.md
- **Commands**: ctx sync, session append
- **Pack SHA**: `c3c0a4a0003f2420`

## 2025-12-30 10:55 UTC
- **Summary**: Applying documentation deprecation fixes (3 files)
- **Files**: docs/plans/2025-12-29-context-pack-ingestion.md, docs/implementation/context-pack-implementation.md, docs/plans/t9-correction-evidence.md
- **Commands**: multi_replace_file_content
- **Pack SHA**: `307e1f35d7b883ec`

## 2025-12-30 10:57 UTC
- **Summary**: Completed documentation deprecation fixes (3 files)
- **Files**: docs/plans/2025-12-29-context-pack-ingestion.md, docs/implementation/context-pack-implementation.md, docs/plans/t9-correction-evidence.md
- **Commands**: trifecta ctx sync, grep
- **Pack SHA**: `7e5a55959d7531a5`

## 2025-12-31 02:05 UTC
- **Summary**: Analyzed Trifecta composition files
- **Files**: _ctx/prime_trifecta_dope.md, _ctx/agent.md, _ctx/session_trifecta_dope.md, skill.md, _ctx/context_pack.json, _ctx/aliases.yaml, _ctx/telemetry/
- **Commands**: ls -la _ctx, rg --files -g trifecta_config.json, sed -n '1, 200p' _ctx/prime_trifecta_dope.md, sed -n '1, 240p' _ctx/agent.md, sed -n '1, 260p' _ctx/session_trifecta_dope.md, sed -n '1, 260p' skill.md
- **Pack SHA**: `9b44486acded5dd2`

## 2025-12-31 02:07 UTC
- **Summary**: Reviewed install_FP.py vs install_trifecta_context.py for repo default
- **Files**: scripts/install_FP.py, scripts/install_trifecta_context.py, src/infrastructure/validators.py
- **Commands**: nl -ba scripts/install_trifecta_context.py, nl -ba scripts/install_FP.py, nl -ba src/infrastructure/validators.py
- **Pack SHA**: `9b44486acded5dd2`

## 2025-12-31 02:10 UTC
- **Summary**: Refined T8 observability tests (rotation fixed) and hardened Telemetry to record discrete event latencies automatically. Fixed MD/lint issues in documentation and tests.
- **Files**: telemetry.py, test_t8_observability.py, t9a_alias_coverage_gate.md
- **Commands**: pytest, ctx sync, ctx stats, replace_file_content
- **Pack SHA**: `c03476483c66f56a`
## 2025-12-31 02:13 UTC
- **Summary**: Plan FP installer improvements
- **Files**: scripts/install_FP.py, scripts/install_trifecta_context.py, src/infrastructure/validators.py, tests/
- **Commands**: rg -n "validate_segment_structure" -S src tests, rg --files -g "*install*" -S tests, rg -n "install_FP" -S
- **Pack SHA**: `9b44486acded5dd2`


## 2025-12-31 02:15 UTC
- **Summary**: Explored /docs/research. Identified MemTech (L0-L3 storage), AGENTS.md (executable constitution), and Progressive Disclosure (L0-L3 levels) as core next-gen Trifecta patterns. Porting MemTech to infrastructure/storage is the immediate priority.
- **Files**: informe-adaptacion-agente_de_codigo.md, Advance context enhance 2 (1).md, agent_factory.md, braindope.md
- **Commands**: ls docs/research, view_file
- **Pack SHA**: \`c03476483c66f56a\`

## 2025-12-31 02:20 UTC
- **Summary**: Rebuilt Mini-RAG index and performed research. Identified Action Plan v1.1: immediate focus on deduplication (-12% token waste) and script refactor, deprioritizing RAG tuning in favor of AST/LSP.
- **Files**: docs/plans/2025-12-30_action_plan_v1.1.md, .mini-rag/config.yaml
- **Commands**: mini-rag index --rebuild, mini-rag query
- **Pack SHA**: \`c03476483c66f56a\`
## 2025-12-31 02:17 UTC
- **Summary**: Improved FP installer with legacy warnings and cli-root validation
- **Files**: src/infrastructure/validators.py, scripts/install_FP.py, tests/unit/test_validators.py, tests/installer_test.py, docs/plans/2025-12-30-fp-installer-unification.md
- **Commands**: uv run pytest tests/installer_test.py -v
- **Pack SHA**: `9b44486acded5dd2`


## 2025-12-31 02:25 UTC
- **Summary**: Comprehensive synthesis of /docs/research. Defined Trifecta v2.0 Architecture: 1) Functional Pipeline (Monads + SHA-256), 2) Multi-tier Storage (MemTech L0-L3), 3) Executable Constitution (AGENTS.md -> ast-grep), 4) Dynamic Resiliency (Fuzzing + Judge Agent). 
- **Files**: micro_saas.md, pipeline_idea.md, fallas.md, adherencia_agente.md, agent_factory.md
- **Commands**: view_file analysis
- **Pack SHA**: \`c03476483c66f56a\`
## 2025-12-31 02:18 UTC
- **Summary**: Fix indentation error in tests/unit/test_validators.py and run requested tests
- **Files**: tests/unit/test_validators.py
- **Commands**: nl -ba tests/unit/test_validators.py, uv run pytest tests/unit/test_validators.py -v, uv run ruff check .
- **Pack SHA**: `9b44486acded5dd2`

## 2025-12-31 02:19 UTC
- **Summary**: Fixed indentation in validators test; ran validators tests; ruff missing
- **Files**: tests/unit/test_validators.py
- **Commands**: uv run pytest tests/unit/test_validators.py -v, uv run ruff check .
- **Pack SHA**: `9b44486acded5dd2`

## 2025-12-31 02:21 UTC
- **Summary**: Installed dev deps to get ruff; ran ruff check (fails with existing issues)
- **Files**: pyproject.toml
- **Commands**: uv sync --extra dev, uv run ruff check .
- **Pack SHA**: `9b44486acded5dd2`


## 2025-12-31 02:30 UTC
- **Summary**: Created Research ROI Matrix analyzing all 11 documents. Prioritized accuracy and reliability (Linter-Driven Control, SHA-256 integrity, Time Travel CAS) over scaling. ROI values assigned per document idea.
- **Files**: research_roi_matrix.md (artifact), docs/research/*
- **Commands**: write_to_file ROI analysis
- **Pack SHA**: \`c03476483c66f56a\`

## 2025-12-31 02:35 UTC
- **Summary**: Reorganized Research ROI Matrix into 5 strategic clusters. Assigned Product Utility scores (1-10) to each area to prioritize real-world value over technical complexity.
- **Files**: research_roi_matrix.md (updated)
- **Commands**: write_to_file cluster analysis
- **Pack SHA**: \`c03476483c66f56a\`
## 2025-12-31 02:26 UTC
- **Summary**: Fixed ruff warnings (treated as bugs) and reran ruff
- **Files**: scripts/ingest_trifecta.py, scripts/install_trifecta_context.py, src/application/context_service.py, src/application/use_cases.py, src/infrastructure/cli.py, tests/test_context_pack.py, tests/unit/test_session_and_normalization.py
- **Commands**: uv run ruff check .
- **Pack SHA**: `9b44486acded5dd2`


## 2025-12-31 02:40 UTC
- **Summary**: Designed Strategic Roadmap v2.0. Ranked 8 implementations by Priority Score (Utility x ROI). Phase 1 established Core reliability; Phases 2-3 focus on intelligence and resilience.
- **Files**: roadmap_v2.md (artifact)
- **Commands**: write_to_file roadmap design
- **Pack SHA**: \`c03476483c66f56a\`
## 2025-12-31 02:28 UTC
- **Summary**: Run full test suite
- **Files**: tests/
- **Commands**: uv run pytest -v
- **Pack SHA**: `9b44486acded5dd2`

## 2025-12-31 02:28 UTC
- **Summary**: Full test suite run
- **Files**: tests/
- **Commands**: uv run pytest -v
- **Pack SHA**: `9b44486acded5dd2`


## 2025-12-31 02:45 UTC
- **Summary**: Documented Trifecta v2.0 Roadmap and Strategic Analysis in the repository. Created dedicated folder with ROI Matrix, Analysis of research documents, and implementation plan.
- **Files**: docs/v2_roadmap/roadmap_v2.md, docs/v2_roadmap/strategic_analysis.md, docs/v2_roadmap/research_roi_matrix.md
- **Commands**: mkdir, cp, write_to_file
- **Pack SHA**: \`c03476483c66f56a\`
