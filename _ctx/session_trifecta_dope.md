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

