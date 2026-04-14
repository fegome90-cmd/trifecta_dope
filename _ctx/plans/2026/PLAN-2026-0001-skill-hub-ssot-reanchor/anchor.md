# Anchor: PLAN-2026-0001-skill-hub-ssot-reanchor

## Objetivo

Re-anclar una única autoridad markdown para `skill_hub` en `main`, independiente de worktrees, stash y archivos locales sueltos, y reconstruir cualquier slice operativo sólo contra ese contrato soberano.

## Autoridad Canónica

- `openspec/specs/skill-hub-authority/spec.md` es el único SSOT semántico para `skill_hub`.
- Este pack existe para re-anclar decisiones y ejecución contra ese SSOT, no para reemplazarlo.

## In Scope

- Declarar `openspec/specs/skill-hub-authority/spec.md` como SSOT único.
- Tratar checkpoints, handoffs, archive reports, worktrees y stash como evidencia subordinada.
- Reconciliar el slice fragmentado únicamente contra ese SSOT antes de retomar implementación o archive.

## Out of Scope

- Crear un segundo SSOT paralelo en `docs/`, `_ctx/` u otra superficie.
- Archivar cambios o publicar PRs mientras la autoridad siga fragmentada.
- Tomar como verdad operativa artefactos SDD, checkpoints o handoffs no respaldados por código real.

## Cierre Operativo e Higiene

- Las ramas, worktrees y stash usados como superficies forenses o de reconstrucción se consideran transitorios.
- Al terminar la reconstrucción y verificar la autoridad única, se DEBEN limpiar o retirar las superficies temporales que ya no aporten evidencia activa.
- Ninguna rama o worktree residual puede quedar presentada como candidata de autoridad para `skill_hub`.
- Esta obligación de cleanup es operativa y de cierre; NO modifica el SSOT semántico definido en `openspec/specs/skill-hub-authority/spec.md`.

## Exit Criteria

- [ ] Existe una referencia explícita y estable al SSOT en `main`.
- [ ] Toda reconstrucción del slice `skill_hub` se evalúa contra ese SSOT único.
- [ ] Ningún worktree, stash o documento derivado se trata como autoridad semántica.
- [ ] Las superficies transitorias usadas durante la reconstrucción quedan limpiadas o explicitamente retiradas al cierre.
