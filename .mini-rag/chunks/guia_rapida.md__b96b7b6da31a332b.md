## ✏️ Cómo Actualizar skill.md

> **IMPORTANTE**: Al actualizar `skill.md`, seguir el proceso TDD de `writing-skills`

**Referencia obligatoria**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`

**Proceso RED-GREEN-REFACTOR:**
1. **RED**: Crear escenario de presión sin skill - documentar violaciones
2. **GREEN**: Escribir skill que aborde esas violaciones específicas
3. **REFACTOR**: Cerrar loopholes y re-verificar

**Iron Law**: `NO SKILL WITHOUT A FAILING TEST FIRST`

**Estructura recomendada de skill.md:**
```yaml
---
name: .
description: Use when working on Verification
---

# .

## Overview
<!-- 1-2 sentences describiendo el propósito -->

## When to Use
<!-- Bullet list de síntomas y casos de uso -->

## Core Pattern
<!-- Patrón principal con ejemplos -->

## Common Mistakes
<!-- Errores comunes + cómo evitarlos -->
```
