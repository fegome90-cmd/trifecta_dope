# TD Middleware: Trifecta WO Integration

**Idea**: TD plugin muestra el WO activo como "session principal"

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     Sidecar (Go TUI)                              │
│                                                               │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │  Plugin TD (modificado)                              │    │
│   │  ┌───────────────────────────────────────────────────────┐    │    │
│   │  │  Lee: _ctx/index/wo_worktrees.json          │    │    │
│   │  │  Filtra: WO con status="running"           │    │    │
│   │  │  Expone: Como ventana TD con nombre WO   │    │    │
│   │  └───────────────────────────────────────────────────────┘    │    │
│   └──────────────────────────────────────────────────────────────┘    │
│                                                              │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  Trifecta CLI (Python)                              │    │
│   │  ─→ Hook actualiza index cuando WO cambia │    │
│   └──────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementación

### Paso 1: Modificar plugin TD en Sidecar

**Archivo**: `/tmp/sidecar/internal/plugins/td/plugin.go`

Agregar método para leer WO activo:

```go
// getActiveWO returns the currently running Work Order from Trifecta index
func (m *Model) getActiveWO() *WorkOrder {
    m.trifectaMutex.RLock()
    defer m.trifectaMutex.RUnlock()

    if m.trifectaIndex == nil {
        return nil
    }

    for _, wo := range m.trifectaIndex.WorkOrders {
        if wo.Status == "running" {
            return &wo
        }
    }
    return nil
}
```

### Paso 2: Mostrar WO activo en UI

Modificar `View()` para inyectar nombre del WO:

```go
func (m *Model) View() string {
    var woName string
    if wo := m.getActiveWO(); wo != nil {
        woName = fmt.Sprintf("[%s]", wo.ID)
    }

    // Existing TD view logic with WO name injected
    // ...
}
```

### Paso 3: Sincronización automática

Cuando WO cambia a "running" → TD lo detecta
Cuando WO cambia a "done" → TD lo oculta

---

## Archivos a Modificar

| Archivo | Modificación |
|---------|-------------|
| `/tmp/sidecar/internal/plugins/td/plugin.go` | Agregar lectura de WO |
| `/tmp/sidecar/internal/plugins/td/types.go` | Agregar tipos WOIndex |
| `/tmp/sidecar/internal/plugins/td/model.go` | Campo: trifectaIndex *WOIndex |

---

## Características

### 1. Detección Automática

- TD lee `_ctx/index/wo_worktrees.json` cada 30s
- Si hay WO con `status="running"`, lo muestra
- Si no hay WO running, funciona normal

### 2. Integración con tmux

- Opción `t` en TD: "Attach to WO session"
- Crea nueva ventana tmux dentro del worktree
- Nombre de ventana: `[WO-ID] <Título>`

### 3. Transiciones de Estado

```
WO-0001: pending    → TD: Normal
WO-0001: running     → TD: Muestra [WO-0001]
WO-0001: done        → TD: Normal (se oculta badge)
```

---

## Data Flow

```
Trifecta                    Sidecar                     TD
   │                           │                          │
   │ take WO                   │                          │
   ▼                           │                          ▼
_hook                        _load                     │
   │                           │  _poll                     │
   ▼                           ▼                          │
export_wo_index.py        read JSON                   getActiveWO()
   │                           │                          │
   ▼                           │                          ▼
_ctx/index/wo_worktrees.json    wo *WorkOrder
   │                           │                          │
   │                           │                          │
   │                           │                          ▼
   │                           │                    View() con [WO-ID]
   │                           │                          │
   └─────────────────────────────────────────────────────────┘
```

---

## Keybindings Propuestos

| Key | Acción | Contexto |
|-----|--------|----------|
| `tw` | Toggle WO window | Solo en TD con WO activo |
| `to` | Open in tmux | Abre sesión en worktree |
| `tc` | Close WO | Cierra ventana WO |

---

## Prerequisites

1. ✅ WO-0011 completado (integración básica)
2. ✅ JSON export funcional
3. ✅ Plugin Trifecta en Sidecar
4. ⏳ Modificar plugin TD (pendiente)

---

## Orden de Implementación

### Fase 1: Shared Types (1 hora)
- Copiar `internal/plugins/trifecta/types.go` a TD
- O reutilizar tipos WOIndex, WorkOrder

### Fase 2: TD Model (1 hora)
- Agregar campo `trifectaIndex *WOIndex`
- Agregar mutex para lectura segura
- Agregar método `getActiveWO()`

### Fase 3: TD View (30 min)
- Modificar `View()` para mostrar badge WO
- Inyectar nombre del WO en header

### Fase 4: Sync Loop (30 min)
- Poll `_ctx/index/wo_worktrees.json` cada 30s
- Recargar index cuando cambie

### Fase 5: Tmux Integration (1 hora)
- Comando para abrir worktree
- Integración con sesiones tmux existentes

---

## Testing

```bash
# 1. Tomar WO
trifecta take WO-0017

# 2. Ver index actualizado
jq '.work_orders[] | select(.status == "running")' _ctx/index/wo_worktrees.json

# 3. Ejecutar Sidecar
cd /tmp/sidecar
./bin/sidecar -project /Users/felipe/.../trifecta_dope

# 4. Presionar TAB hasta TD
# Debería mostrar [WO-0017]
```

---

**Estimated**: 3-4 horas de desarrollo
