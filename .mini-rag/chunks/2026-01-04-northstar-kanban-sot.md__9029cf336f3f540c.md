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
