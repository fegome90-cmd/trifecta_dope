# . - Trifecta Documentation

> **Trifecta System**: Este segmento usa el sistema Trifecta para comprensión rápida por agentes de código.

## 📁 Estructura

```
./
├── readme_tf.md                 # Este archivo - guía rápida
├── skill.md                     # Reglas y contratos (MAX 100 líneas)
└── _ctx/                        # Context resources
    ├── prime_..md # Lista de lectura obligatoria
    ├── agent.md                 # Stack técnico y configuración
    └── session_..md # Log de handoffs (runtime)
```

## 🚀 Flujo de Onboarding (Para Agentes)

1. **Leer `skill.md`** — Reglas, roles, y contratos del segmento
2. **Leer `_ctx/prime_..md`** — Lista de documentos obligatorios
3. **Leer `_ctx/agent.md`** — Stack técnico, configuración, y gates

> [!CAUTION]
> **No ejecutes código sin completar los 3 pasos anteriores.**

## 📊 Perfiles de Output

| Perfil | Propósito | Contract |
|--------|-----------|----------|
| `diagnose_micro` | Máximo texto, código ≤3 líneas | `code_max_lines: 3` |
| `impl_patch` | Patch con verificación | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations]` |
| `plan` | DoD + pasos (sin código) | `forbid: [code_blocks]` |
| `handoff_log` | Bitácora + handoff | `append_only: true` |

## 🔄 Actualización

- **Prime**: Actualizar cuando se agregue/modifique documentación del segmento
- **Session**: Actualizar después de cada handoff entre sesiones
- **Agent**: Revisar cuando cambie el stack técnico o configuración
- **Skill**: Actualizar siguiendo **superpowers:writing-skills** (ver abajo)

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

## 📖 Referencias

- **Scope**: Verification
- **Default Profile**: `impl_patch`
- **Last Verified**: 2025-12-29
- **Repo Root**: `/Users/felipe_gonzalez/Developer/agent_h`
- **Writing Skills**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`
