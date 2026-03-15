# Trifecta_Dope - Trifecta Documentation

> **Trifecta System**: Este segmento usa el sistema Trifecta para comprension rapida por agentes de codigo.

## [FILE] Estructura

```
trifecta_dope/
|-- readme_tf.md                 # Este archivo - guia rapida
|-- skill.md                     # Reglas y contratos (MAX 100 lineas)
|__ _ctx/                        # Context resources
    |-- prime_trifecta_dope.md # Lista de lectura obligatoria
    |-- agent.md                 # Stack tecnico y configuracion
    |__ session_trifecta_dope.md # Log de handoffs (runtime)
```

## [CLI] CLI Usage

### Opcion A: alias con TRIFECTA_CLI_ROOT
```bash
export TRIFECTA_CLI_ROOT="/absolute/path/to/trifecta_dope"
alias trifecta='uv --directory "$TRIFECTA_CLI_ROOT" run trifecta'
```

### Opcion B: directo

```bash
uv --directory "$TRIFECTA_CLI_ROOT" run trifecta ctx sync --segment .
uv --directory "$TRIFECTA_CLI_ROOT" run trifecta ctx search --segment . --query "parser" --limit 6
uv --directory "$TRIFECTA_CLI_ROOT" run trifecta load --segment . --mode fullfiles --task "My task"
```

## [GO] Flujo de Onboarding (Para Agentes)

1. **Leer `skill.md`** - Reglas, roles, y contratos del segmento
2. **Leer `_ctx/prime_trifecta_dope.md`** - Lista de documentos obligatorios
3. **Leer `_ctx/agent.md`** - Stack tecnico, configuracion, y gates

> [!CAUTION]
> **No ejecutes codigo sin completar los 3 pasos anteriores.**

## [DATA] Perfiles de Output

| Perfil | Proposito | Contract |
|--------|-----------|----------|
| `diagnose_micro` | Maximo texto, codigo <=3 lineas | `code_max_lines: 3` |
| `impl_patch` | Patch con verificacion | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations]` |
| `plan` | DoD + pasos (sin codigo) | `forbid: [code_blocks]` |
| `handoff_log` | Bitacora + handoff | `append_only: true` |

## [SYNC] Actualizacion

- **Prime**: Actualizar cuando se agregue/modifique documentacion del segmento
- **Session**: Actualizar despues de cada handoff entre sesiones
- **Agent**: Revisar cuando cambie el stack tecnico o configuracion
- **Skill**: Actualizar siguiendo **superpowers:writing-skills** (ver abajo)

## [EDIT] Como Actualizar skill.md

> **IMPORTANTE**: Al actualizar `skill.md`, seguir el proceso TDD de `writing-skills`

**Referencia obligatoria**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`

**Proceso RED-GREEN-REFACTOR:**
1. **RED**: Crear escenario de presion sin skill - documentar violaciones
2. **GREEN**: Escribir skill que aborde esas violaciones especificas
3. **REFACTOR**: Cerrar loopholes y re-verificar

**Iron Law**: `NO SKILL WITHOUT A FAILING TEST FIRST`

**Estructura recomendada de skill.md:**
```yaml
---
name: trifecta_dope
description: Use when working on Scope
---

# Trifecta_Dope

## Overview
<!-- 1-2 sentences describiendo el proposito -->

## When to Use
<!-- Bullet list de sintomas y casos de uso -->

## Core Pattern
<!-- Patron principal con ejemplos -->

## Common Mistakes
<!-- Errores comunes + como evitarlos -->
```

## [REF] Referencias

- **Scope**: Scope
- **Default Profile**: `impl_patch`
- **Last Verified**: 2026-03-06
- **Repo Root**: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope`
- **Writing Skills**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`
