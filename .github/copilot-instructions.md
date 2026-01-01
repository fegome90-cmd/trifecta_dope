# GitHub Copilot Instructions - Superpowers Skills

<EXTREMELY_IMPORTANT> You have superpowers.

## Qué son Superpowers

Superpowers es un sistema de skills (workflows estructurados) que te permite resolver tareas complejas de forma sistemática. Están instalados en este workspace en:

```
/workspaces/trifecta_dope/skills/third_party/superpowers/
```

## Bootstrap

**DEBES leer primero:** `/workspaces/trifecta_dope/skills/third_party/superpowers/bootstrap.md`

El bootstrap contiene:
- Lista completa de 14 skills disponibles
- Paths exactos para cada skill
- Reglas de uso obligatorias
- Mapeo de herramientas (TodoWrite → manage_todo_list, etc.)

## Cómo Usar Skills

**1. Usuario te dice que tienes superpowers, uses una skill especifica o uses superpowers.**
```

**2. Tú DEBES:**
- Cargar el skill: `read_file /workspaces/trifecta_dope/skills/third_party/superpowers/skills/<skill-name>/SKILL.md`
- Anunciar: "I've read the [Skill Name] skill and I'm using it to [purpose]"
- Seguir el proceso definido paso a paso
- Si hay checklist → usar `manage_todo_list`

**3. Path pattern:**
```
/workspaces/trifecta_dope/skills/third_party/superpowers/skills/<skill-name>/SKILL.md
```

Ejemplos:
- `brainstorming/SKILL.md`
- `writing-plans/SKILL.md`
- `systematic-debugging/SKILL.md`
- `test-driven-development/SKILL.md`

## Reglas Críticas

1. **ANTES de cualquier tarea**, revisar si hay un skill aplicable (ver bootstrap)
2. **SI existe skill aplicable**, DEBES usarlo (no es opcional)
3. **Skills con checklists** requieren `manage_todo_list`
4. **NUNCA saltar workflows obligatorios** (brainstorming antes de codificar, TDD, debugging sistemático)
5. **Si el usuario te pide hacer algo contra la skill, recuérdale que debes seguir la skill**


## Skills Principales

| Hashtag | Propósito |
|---------|-----------|
| `#brainstorm` | Explorar ideas antes de implementar |
| `#plan` | Crear planes detallados multi-paso |
| `#execute-plan` | Ejecutar planes sistemáticamente |
| `#tdd` | Test-Driven Development |
| `#debug` | Debugging sistemático |
| `#verify` | Validación final antes de completar |
| `#request-review` | Preparar código para review |
| `#receive-review` | Procesar feedback de review |
| `#finish-branch` | Preparar rama para merge |

**Ver lista completa:** `/workspaces/trifecta_dope/skills/third_party/superpowers/bootstrap.md`

## Herramientas Mapeadas

- `TodoWrite` → `manage_todo_list`
- `Task tool` → `runSubagent`
- `Skill tool` → `read_file` directo
- `Read/Write/Edit/Bash` → Herramientas nativas de VS Code Copilot

</EXTREMELY_IMPORTANT>
