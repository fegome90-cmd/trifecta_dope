---
name: skill-hub-ssot-reanchor
description: Re-ancla el SSOT markdown de skill_hub en main antes de reconstruir slices fragmentados.
---

## Carga

anchor.md → SKILL.md → resources/

## Reglas

1. Si `anchor.md` contradice a otro documento, gana `anchor.md`.
2. El SSOT semántico para `skill_hub` vive en `openspec/specs/skill-hub-authority/spec.md`.
3. Ningún cambio de scope o archive se aprueba sin reconciliar primero el slice real contra el SSOT.
4. Fail-closed: si la evidencia no coincide con el código real, se detiene el flujo.

## Referencias

- resources/agents.md — roles y límites de decisión
- resources/prime.md — pre-flight gates para re-anchor
- openspec/specs/skill-hub-authority/spec.md — contrato soberano
