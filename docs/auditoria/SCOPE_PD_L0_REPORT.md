# SCOPE_PD_L0_REPORT.md

## A) Inventario de componentes

| Componente | Archivo(s) | Función(es) clave | Rol |
|------------|------------|-------------------|-----|
| **ctx sync** | `src/infrastructure/cli.py` | `sync()` | Macro: Build + Validate. Orquestador de indexación. |
| **prime** | `_ctx/prime_*.md` | N/A | Lista de lectura obligatoria y prioritizada (SOT para el agente). |
| **context_pack** | `_ctx/context_pack.json` | `ContextPack` (model) | Almacén de chunks indexados y metadatos del segmento. |
| **chunking** | `src/application/use_cases.py` | `BuildContextPackUseCase` | Ingesta de archivos. En v1 usa `whole_file`. |
| **index** | `context_pack.json` | `index` field | Mapa de búsqueda rápida (preview, title, token_est). |
| **skeleton** | `src/application/context_service.py` | `_skeletonize()` | Genera vista estructural (headers + signatures) on-demand. |
| **LSP hooks** | `src/infrastructure/cli_ast.py` | `symbols()`, `hover()` | Puente hacia el LSP Daemon para info técnica profunda. |
| **telemetry events**| `src/infrastructure/telemetry.py` | `event()`, `flush()` | Registro de latencia, hits y uso de tokens. |

---

## B) PD: Evidencia de implementación

### 1. ¿Dónde se decide “leer poco vs leer más”?
La lógica reside en `src/application/context_service.py:86` (`ContextService.get`). Se basa en el parámetro `mode` (`raw`, `excerpt`, `skeleton`) y el `budget_token_est`.

### 2. ¿Noción de niveles (L0/L1/L2)?
- **Documentada**: El `README.md` (L112-116) define umbrales de Score (`<0.6 L0`, etc.).
- **Real (Código)**: `ContextService` no usa los umbrales de score todavía. Implementa PD mediante:
  - `mode="excerpt"`: Primeras 25 líneas (`L1` parcial).
  - `mode="skeleton"`: Estructura (`L0` técnico).
  - `mode="raw"`: Contenido total con guardrail de presupuesto.

### 3. Límites y Truncado
- **Presupuesto**: Default 1200–1500 tokens (`budget_token_est`).
- **Truncado de Chunks**: Si un chunk individual excede el presupuesto en modo `raw`, se reduce a 20 líneas con una nota (Backpressure).
- **Truncado de Lista**: `ctx get` deja de procesar IDs si ya alcanzó el presupuesto.

### Snippets Relevantes

**src/application/context_service.py:100-117**
```python
        for chunk_id in ids:
            chunk = chunk_map.get(chunk_id)
            if not chunk: continue

            # Progressive Disclosure logic
            text = chunk.text
            if mode == "excerpt":
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                excerpt_lines = lines[:25]
                text = "\n".join(excerpt_lines)
                if len(lines) > 25:
                    text += "\n\n... [Contenido truncado, usa mode='raw' para ver todo]"
            elif mode == "skeleton":
                text = self._skeletonize(text)
            elif mode == "raw":
                token_est = len(text) // 4
                if total_tokens + token_est > budget:
                    # Fallback to excerpt with note
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    text = "\n".join(lines[:20]) + "\n\n> [!NOTE]\n> Chunk truncado por presupuesto..."
```

---

## C) L0 Skeleton: Definición real

- **Artefacto**: Es una transformación funcional del `text` del chunk realizada en tiempo de ejecución por `ContextService._skeletonize`.
- **Campos incluidos**:
  - Headings Markdown (`#`).
  - Bloques de código (```).
  - Primeras líneas de bloques de código que contienen signatures (`def`, `class`, `interface`, `function`, `const`, `var`).
- **Pipeline**: `ctx get --mode skeleton` -> `ContextService.get` -> `_skeletonize`.
- **NO incluye**: Implementaciones de funciones, comentarios de línea (no-headers), imports masivos.

### Ejemplo real (Salida de `ctx get --mode skeleton`)
```
## Overview
## ⚠️ ONBOARDING OBLIGATORIO ⚠️
## Core Rules
### Session Evidence Protocol
## When to Use
### The Context Cycle (Search -> Get)
```

---

## D) Experimentos mínimos

### 1. `uv run trifecta ctx sync -s .`
```
🔄 Running build...
✅ Build complete. Validating...
✅ Validation Passed
🔄 Regenerating stubs...
   ✅ Regenerated: repo_map.md, symbols_stub.md
```

### 2. `uv run trifecta ctx search -s . -q "Verification"`
```
Search Results (2 hits):
1. [skill:03ba77a5e8] skill.md
   Score: 0.50 | Tokens: ~634
   Preview: ---
name: trifecta_dope
...
2. [agent:abafe98332] agent_trifecta_dope.md
   Score: 0.50 | Tokens: ~1067
...
```

### 3. `uv run trifecta ctx get -s . -i "skill:03ba77a5e8" --mode excerpt`
```
Selected Chunks (1):
1. [skill:03ba77a5e8] skill.md
... [Primeras 25 líneas] ...
... [Contenido truncado, usa mode='raw' para ver todo]
Total Tokens: ~634
```

### 4. LSP Control
- **Evidencia**: No hay flag `LSP_OFF` global. El control es reactivo: si `client.is_ready()` es falso, se emite `lsp.fallback`.
- **Simulación**: Matar el daemon (`rm /tmp/hemdov_debug.sock`) fuerza el fallback a AST automático en el siguiente comando `ast symbols`.

---

## E) Conclusión de scope

- **PD existe**: **PARCIAL**. Está implementado el mecanismo de *modos* (excerpt/skeleton) y *presupuesto*, pero falta el trigger automático basado en *Score* que menciona el README.
- **L0 Skeleton cumple**: **SÍ**. El skeletonizador es determinista y extrae firmas y estructura correctamente.
- **Gaps concretos**:

| Gap | Dónde tocar | Riesgo si no se corrige | Tamaño |
|-----|-------------|-------------------------|--------|
| **1. Score-based Auto PD** | `ContextService.get` | El agente debe elegir manualmente el modo; mayor carga cognitiva. | M |
| **2. Skeleton Signatures (JS/TS)** | `ContextService._skeletonize`| Soporte pobre para otros lenguajes fuera de Python (keywords hardcoded). | S |
| **3. Search keyword recall** | `ContextService.search` | Chunks relevantes no se encuentran si el término no está en el preview truncado. | M |
| **4. Budget Backpressure Hardening**| `ContextService.get` | Sigue acumulando tokens hasta pasarse; el fallback a excerpt es solo para el *último* chunk que no cabe. | S |
| **5. Cross-file Skeleton Index** | `context_pack.json` index | El index no guarda el skeleton pre-calculado; obliga a cargar el `text` completo para skeletonizar. | L |
