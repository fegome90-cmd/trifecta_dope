#### Contenido Clave:
- **Líneas 7-26**: [Arquitectura General](#1-aráctica-general)
  - Diagrama de componentes CLI → ContextService → LSP Daemon
  - Flujo de datos PD L0/L1

- **Líneas 28-72**: [Capa L0: Skeleton Mode](#2-capa-l0-skeleton-mode)
  - Definición: `context_service.py:265-301`
  - Ejemplo entrada/salida skeletonización
  - Tabla de modos: raw/excerpt/skeleton

- **Líneas 74-115**: [Capa L1: AST y LSP](#3-capa-l1-ast-y-lsp)
  - LSP Daemon: socket IPC, 180s TTL
  - AST Parser: stub implementation
  - Comandos CLI: `ast symbols`, `ast hover`

- **Líneas 117-122**: [Capa L2: Estado Actual](#4-capa-l2-estado-actual)
  - ❌ NO EXISTE como capa arquitectónica
  - `mode="raw"` con budget alto = L2 "de facto"

- **Líneas 134-148**: [Gaps Identificados](#6-gaps-y-recomendaciones)
  - Score-based Auto PD (ALTA)
  - LSP Real Output (MEDIA)
  - Search keyword recall (MEDIA)

---
