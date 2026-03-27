# Auditoría del Plan v2: Daemon + LSP

**Fecha**: 2026-03-22
**Método**: Auditoría manual (tmux-plan-auditor timeout sin output)
**Input**: `docs/daemon-lsp-scope/daemon_lsp_operationalization_plan_v2.md`

---

## 1. Lógica del plan

### Ambigüedades detectadas

| # | Ambigüedad | Ubicación | Severidad |
|---|-----------|-----------|-----------|
| 1 | "resolver runtime.db" dice "eliminar check o crear automáticamente" pero no decide cuál | Fase 2 | Media |
| 2 | "spawn LSP al inicio o lazy" como decisión pendiente | Fase 3 | Media |
| 3 | "file lock o socket bind" como decisión pendiente | Fase 4 | Baja |

### Alcance: ✅ Correcto

- Foco exclusivo daemon + LSP
- No propone fixes tempranos
- No declara production ready

### Criterios: ⚠️ Mejorable

- Cada fase tiene cerrado local/técnico ✅
- Falta criterio cuantificable en Fase 1

---

## 2. Calidad

- No hay refactors grandes ✅
- Tabla de verdad "ready" no coincide con health check real (health no usa PING) ⚠️
- Matriz ownership dice "locks implícito" pero daemon run usa socket bind, no file lock ⚠️

---

## 3. Silent failures

| Escenario | ¿Manejado? | ¿Planificado? |
|-----------|-----------|---------------|
| pyright no instalado | No | Sí (Fase 3) |
| LSP crash durante request | No | **NO** |
| Socket bind falla | Parcial | Sí (Fase 4) |

**Hallazgo crítico**: No se aborda LSP crash recovery.

---

## 4. Testing

Tests existentes cubren Fase 2-4 ✅

Tests que faltan:

- daemon run responde PING/HEALTH/SHUTDOWN (Fase 2)
- daemon run + LSPClient integración (Fase 3)
- LSP crash recovery (Fase 3)
- Concurrent daemon start (Fase 4)

---

## Veredicto

Plan sólido. Gaps principales: LSP crash recovery y tests de integración.

## Recomendaciones

1. Fase 2: decidir explícitamente runtime.db (eliminar o crear)
2. Fase 3: agregar criterio para LSP crash durante request
3. Fase 3: agregar test de integración como criterio de cierre
