# Agents: PLAN-2026-0001-skill-hub-ssot-reanchor

## Roles

### Arquitecto
- Declara y protege la autoridad única del sistema.
- Rechaza SSOTs paralelos, narrativas competidoras y fallback ambiguo.

### Ejecutor
- Reconstruye slices sólo contra el SSOT declarado.
- No promueve stash, worktrees o handoffs a autoridad semántica.

## Autoridad

- SSOT semántico: `openspec/specs/skill-hub-authority/spec.md`
- `anchor.md` gobierna este plan; no reemplaza el SSOT del repo.

## Reglas de Interacción

1. El Arquitecto define la autoridad; el Ejecutor implementa contra ella.
2. Si aparece evidencia fragmentada, se clasifica como evidencia, no como contrato.
3. Ningún archive, commit o PR antes de resolver la superficie autoritativa.
