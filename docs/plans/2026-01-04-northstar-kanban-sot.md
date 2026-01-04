# Trifecta Northstar Kanban SOT - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear un Kanban vivo que actúe como Source of Truth (SOT) del proyecto Trifecta, rastreando el avance de cada pilar del Northstar.

**Architecture:** Auditar exhaustivamente el repositorio con las herramientas CLI (Trifecta, Mini-RAG), verificar los 3 archivos MD core + JSON asociados, y generar un Kanban compatible con extensiones de visualización.

**Tech Stack:** Trifecta CLI, Mini-RAG CLI, VSCode Extension (Kanban.md or Markdown Kanban), Markdown Tables.

---

## Pre-Requisitos

| Herramienta | Comando Verificación | Propósito |
| :--- | :--- | :--- |
| Trifecta CLI | `uv run trifecta --help` | Búsqueda PCC y navegación |
| Mini-RAG CLI | `mini-rag --help` | Análisis de documentación (si disponible) |
| VSCode | n/a | Renderizado del Kanban |

---

## Task 1: Auditoría Exhaustiva del Repositorio

**Files:**
- Read: `_ctx/prime_trifecta_dope.md`
- Read: `_ctx/agent_trifecta_dope.md`
- Read: `_ctx/session_trifecta_dope.md`
- Read: `_ctx/context_pack.json`
- Read: All `docs/v2_roadmap/*.md`
- Read: All `docs/plans/*.md` (Jan 2026 and later)
- Read: All `docs/technical_reports/*.md`

**Step 1.1: Sync Context Pack**

Run: `uv run trifecta ctx sync -s .`
Expected: `✅ Validation Passed`

**Step 1.2: Search for Northstar Keywords**

Run: `uv run trifecta ctx search -s . -q "Northstar roadmap v2 priority"`
Expected: Hits on `roadmap_v2.md`, `north-star-validation.md`

**Step 1.3: Search for Implementation Status Keywords**

Run: `uv run trifecta ctx search -s . -q "implemented complete done verified"`
Expected: Hits on technical reports and session logs

**Step 1.4: Extract Roadmap Items**

Manually read `docs/v2_roadmap/roadmap_v2.md` and extract:
- All items in "Cuadro de Priorización"
- All items in "Fases de Implementación"
- Success Metrics

**Step 1.5: Verify Trifecta Core Files (3+1)**

| File | Expected Format | Validation |
| :--- | :--- | :--- |
| `_ctx/prime_trifecta_dope.md` | YAML frontmatter + path list | `segment:` field exists |
| `_ctx/agent_trifecta_dope.md` | YAML frontmatter + Tech Stack | `scope:` field exists |
| `_ctx/session_trifecta_dope.md` | Session log entries | `## YYYY-MM-DD` headers |
| `_ctx/context_pack.json` | JSON Schema v1 | `schema_version: 1` |

Run: `jq '.schema_version, .segment' _ctx/context_pack.json`
Expected: `1` and `"trifecta_dope"`

---

## Task 2: Investigar Opciones de Visualización

**Step 2.1: Evaluar Extensiones VSCode**

| Extensión | Característica Clave | Formato Archivo |
| :--- | :--- | :--- |
| **Markdown Kanban** | Drag-and-drop, 2-way sync | `.kanban.md` or standard `.md` |
| **Kanban.md** | Theme adaptation, priority/tags | `.kanban.md` |
| **Taskboard** | Renders from `TODO.md` | Standard `TODO.md` |

**Recomendación:** Usar **Markdown Kanban** por su bidireccionalidad y soporte de prioridades.

**Step 2.2: Definir Formato del Kanban**

Crear archivo `TRIFECTA_NORTHSTAR_KANBAN.kanban.md` con formato compatible:

```markdown
# Trifecta Northstar Kanban

## 🏁 VERIFIED
- [x] Result Monad (FP) #priority:high #phase:1
- [x] PCC Core (Search/Get) #priority:high #phase:1

## ⚙️ IN PROGRESS
- [ ] Linter-Driven Loop #priority:high #phase:1

## 📝 BACKLOG
- [ ] Property-Based Testing #priority:med #phase:2
```

**Step 2.3: Alternativa - Dashboard HTML Simple**

Si la extensión no es viable, crear `docs/dashboard/kanban.html` con:
- Columnas CSS Grid
- Datos embebidos desde JSON
- Actualización manual vía script

---

## Task 3: Mapear Items del Roadmap a Código

**Files:**
- Modify: `docs/v2_roadmap/TRIFECTA_NORTHSTAR_KANBAN.md` (o `.kanban.md`)

**Step 3.1: Para cada item del roadmap, verificar estado en código**

Para cada item, ejecutar:

```bash
# Ejemplo: Verificar "Result Monad"
uv run trifecta ctx search -s . -q "Result Monad Ok Err"
rg "class Ok" src/
```

**Step 3.2: Crear matriz de trazabilidad**

| Item Roadmap | Path Código | Test Path | Estado |
| :--- | :--- | :--- | :--- |
| Result Monad | `src/domain/result.py` | `tests/unit/test_result_monad.py` | ✅ |
| North Star Gate | `src/infrastructure/validators.py` | `tests/unit/test_validators_fp.py` | ✅ |
| Progressive Disclosure | `src/application/context_service.py` | `tests/unit/test_chunking.py` | ✅ |

**Step 3.3: Identificar Ghost Implementations**

Buscar clases sin llamadas en la aplicación:

```bash
rg "class SymbolSelector" src/  # Existe
rg "SymbolSelector" src/application/use_cases.py  # ¿Se usa?
```

---

## Task 4: Generar Kanban Final

**Files:**
- Create: `docs/v2_roadmap/TRIFECTA_NORTHSTAR_KANBAN.kanban.md`

**Step 4.1: Escribir archivo Kanban**

Usar el formato definido en Task 2.2 con todos los items mapeados en Task 3.

**Step 4.2: Añadir metadatos de trazabilidad**

```markdown
<!-- SOT_META
last_audit: 2026-01-04
auditor: Antigravity (Deep Audit)
tools: trifecta ctx search, Mini-RAG, rg
-->
```

**Step 4.3: Commit**

```bash
git add docs/v2_roadmap/TRIFECTA_NORTHSTAR_KANBAN.kanban.md
git commit -m "feat(kanban): Add Northstar SOT Kanban with traceability"
```

---

## Task 5: Verificación Final

**Step 5.1: Verificar renderizado en VSCode**

1. Instalar extensión "Markdown Kanban" o "Kanban.md"
2. Abrir `TRIFECTA_NORTHSTAR_KANBAN.kanban.md`
3. Verificar que las columnas y items se renderizan correctamente

**Step 5.2: Verificar sincronización bidireccional**

1. Mover un item de "BACKLOG" a "IN PROGRESS" en la vista gráfica
2. Verificar que el archivo `.kanban.md` se actualiza
3. Revertir el cambio

**Step 5.3: Documentar en Session**

```bash
uv run trifecta session append -s . --summary "Created Northstar SOT Kanban" --files "docs/v2_roadmap/TRIFECTA_NORTHSTAR_KANBAN.kanban.md"
```

---

## Resumen de Entregables

| Entregable | Path | Descripción |
| :--- | :--- | :--- |
| **Kanban SOT** | `docs/v2_roadmap/TRIFECTA_NORTHSTAR_KANBAN.kanban.md` | Tablero rastreable |
| **Matriz Trazabilidad** | (inline en Kanban o separado) | Item ↔ Código |
| **Session Entry** | `_ctx/session_trifecta_dope.md` | Log de la auditoría |

---

**Plan completo guardado. Dos opciones de ejecución:**

**1. Subagent-Driven (esta sesión)** — Despacho subagent fresco por task, review entre tasks, iteración rápida

**2. Parallel Session (separada)** — Nueva sesión con executing-plans, ejecución batch con checkpoints

**¿Cuál prefieres?**
