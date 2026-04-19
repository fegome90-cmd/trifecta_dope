# Prime: PLAN-2026-0001-skill-hub-ssot-reanchor

## Pre-flight Gates

### Gate 1 — Autoridad
- **Condición:** Identifiqué un único SSOT para `skill_hub`.
- **Evidencia:** `openspec/specs/skill-hub-authority/spec.md` citado explícitamente.
- **Si falla:** Abortá. No reconciliar múltiples superficies ad hoc.

### Gate 2 — Superficie real
- **Condición:** Separé autoridad, evidencia y basura local.
- **Evidencia:** branch/worktree/stash/untracked clasificados.
- **Si falla:** No tocar código ni SDD.

### Gate 3 — Trazabilidad
- **Condición:** Toda afirmación sobre implementación se contrasta con código real.
- **Evidencia:** archivo y líneas verificadas.
- **Si falla:** Rebajar o corregir la narrativa.

### Gate 4 — Cierre seguro
- **Condición:** No voy a archivar ni publicar con autoridad fragmentada.
- **Evidencia:** decisión explícita registrada.
- **Si falla:** detener el flujo.
