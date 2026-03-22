# Auditoría de Boundary - Graph ↔ PCC/Context Pack

Fecha: 2026-03-13
Objetivo: Determinar punto de integración seguro entre Graph y PCC sin romper paradigma meta-first

---

## A. Resumen Ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existe link símbolo→chunk? | ❌ NO existe actualmente |
| ¿source_path es estable? | ⚠️ Parcialmente - cambia con pack rebuild |
| ¿chunk_ids son persistentes? | ❌ Efímeros - basados en hash de contenido |
| ¿El boundary es viable hoy? | ⚠️ Requiere endurecimiento previo |

---

## B. Flujo Real de Context Pack

### Build Process

```
trifecta ctx build / sync
    → BuildContextPackUseCase.execute(target_path)
        ├── 1. Cargar trifecta_config.json (si existe)
        ├── 2. Derivar segment_id desde config o dirname
        ├── 3. Localizar archivos fuente:
        │   ├── skill.md (primario)
        │   ├── agent_{segment_id}.md
        │   ├── prime_{segment_id}.md
        │   ├── session_{segment_id}.md
        │   └── refs desde Prime (links en formato [link](path))
        └── 4. Escanear repo:
            ├── docs/**/*.md
            ├── src/**/*.py
            ├── skills/**/*.md
            ├── config/**/*.{yaml,json,toml}
            └── tests/**/*.py

        → Para cada archivo: crear ContextChunk (whole_file)
```

### Archivo Generado

```
_ctx/
├── context_pack.json
│   ├── schema_version: 1
│   ├── segment: "segment_id"
│   ├── created_at: "ISO timestamp"
│   ├── digest: "" (vacío en código)
│   ├── source_files: [SourceFile]
│   │   ├── path: "relative/path"
│   │   ├── sha256: "hash"
│   │   ├── mtime: float
│   │   └── chars: int
│   ├── chunks: [ContextChunk]
│   │   ├── id: "kind:hash10"
│   │   ├── doc: "kind"
│   │   ├── title_path: ["hierarchical", "path"]
│   │   ├── text: "full content"
│   │   ├── char_count: int
│   │   ├── token_est: int
│   │   └── source_path: "relative/path"
│   └── index: [ContextIndexEntry]
│       ├── id: "kind:hash10"
│       ├── title_path_norm: "norm path"
│       ├── preview: "first 200 chars"
│       └── token_est: int
└── context_pack.json.sha256
```

---

## C. Contrato Actual de Chunks

### Chunk ID Generation

De [`use_cases.py:507-508`](src/application/use_cases.py:507):

```python
content_hash = hashlib.sha1(id_input.encode(), usedforsecurity=False).hexdigest()[:10]
chunk_id = f"{doc_type}:{content_hash}"
```

Donde `id_input` = `doc_type + content` (el contenido completo del archivo).

### Campos Relevantes para Linking

| Campo | Origen | Estabilidad |
|-------|--------|-------------|
| `id` | `sha1(content)[:10]` | ❌ Efímero - cambia si contenido cambia |
| `doc` | Tipo de archivo (`skill`, `agent`, `prime`, `repo:path`) | ✅ Estable |
| `source_path` | Relative path desde target root | ⚠️ Parcial - cambia si pack rebuild |
| `text` | Contenido completo | ❌ Efímero |
| `title_path` | Ruta jerárquica | ⚠️ Parcial |

### Clasificación de Chunks

De [`use_cases.py:912-926`](src/application/use_cases.py:912):

```python
def _classify_hit_target(self, chunk_id: str) -> str:
    if chunk_id.startswith("skill:"): return "skill"
    elif chunk_id.startswith("prime:"): return "prime"
    elif chunk_id.startswith("session:"): return "session"
    elif chunk_id.startswith("agent:"): return "agent"
    elif chunk_id.startswith("ref:"): return "ref"
    elif chunk_id.startswith("repo:"): return "repo"
```

---

## D. Viabilidad de Linking Símbolo↔Chunk

### Análisis de Campos

| Campo Símbolo (AST) | Campo Chunk (Pack) | Link Viable? |
|--------------------|-------------------|---------------|
| `file_path` | `source_path` | ⚠️ Requiere normalización |
| `name` | ❌ No existe | ❌ No hay mapping |
| `qualified_name` | ❌ No existe | ❌ No hay mapping |
| `start_line` | ❌ No existe | ❌ No hay mapping |
| `end_line` | ❌ No existe | ❌ No hay mapping |
| `kind` | `doc` (parcial) | ⚠️ Solo para "repo:*.py" |

### ¿Existe Base Suficiente?

**NO existe actualmente** ningún mecanismo de linking entre:

- Símbolos extraídos por `SkeletonMapBuilder` (AST)
- Chunks indexados en `context_pack.json`

### Lo que Sería Necesario

| Componente | Estado Actual | Requerido |
|------------|--------------|-----------|
| Symbol → File mapping | ✅ Existe en AST | Extender a range |
| File → Chunk mapping | ⚠️ Parcial (source_path) | Agregar line ranges |
| Chunk version tracking | ❌ No existe | Agregar hash/versioning |
| Stable IDs | ❌ chunk_ids efímeros | Usar source_path + range |

---

## E. Riesgos de Phantom/Stale Links

### Phantom Links (Links que apuntan a nada)

| Riesgo | Probabilidad | Trigger |
|--------|-------------|---------|
| Chunk fue deleteado del pack | Alta | `ctx build` sin contenido previo |
| source_path cambió | Alta | Rename de archivo |
| Contenido cambió (hash diferente) | Alta | Cualquier edición |
| Pack fue regenerado | Alta | `ctx sync` / `ctx build` |

### Stale Links (Links a contenido obsoleto)

| Riesgo | Probabilidad | Trigger |
|--------|-------------|---------|
| Contenido cambió pero ID no cambió | ❌ No aplica | chunk_id es hash → siempre cambia |
| Archivo renombrado | Alta | source_path mismatch |

### El Problema Fundamental

```
chunk_id = sha1(doc_type + content)[:10]
```

Este diseño **intencionalmente** hace los IDs efímeros porque:

1. El contenido puede cambiar
2. El pack se regenera frecuentemente
3. No hay promesa de estabilidad

Esto es **correcto para PCC** porque:

- Chunks son evidencia textual, no punteros estructurales
- El sistema NO debe confiar en IDs persistentes
- La referencia canónica es el **contenido**, no el ID

---

## F. Boundary Correcto para Graph

### Lo que Graph PUEDE entregar

| Entrega | Por qué es seguro |
|---------|------------------|
| **Señales de ranking** | Graph dice "este símbolo es más importante" sin enviar texto |
| **Navigational hints** | "Usa ctx get para este chunk_id" sin generar prompt |
| **Callers/callees info** | "Esta función llama a X" sin enviar código |
| **Impact analysis** | "Cambiar Y afecta Z" como señal, no como contexto |

### Lo que Graph NO DEBE entregar

| Entrega | Por qué es riesgoso |
|---------|------------------|
| **Texto denso para prompt** | Rompe paradigma PCC - enviar contexto en lugar de punteros |
| **Chunk retrieval** | Duplica ctx get - debe usar API existente |
| **Generación de contexto** | Confunde rol: Graph es señal, no proveedor de texto |
| **Serialización de código** | Envía código en lugar de punteros |

### Boundary Contract Propuesto

```
Graph (señal) → PCC (decisión) → Context Pack (evidencia)

Flujo correcto:
1. Agente pregunta "dónde está X?"
2. PCC consulta Graph: "¿qué sabe de X?"
3. Graph retorna SEÑALES (no texto):
   - {symbol: "X", importance: 0.9, callers: ["A"], callees: ["B"]}
4. PCC decide:
   - Si necesita evidencia → ctx get para chunk_ids relevantes
   - Si necesita más → ctx search con términos de Graph
5. Context Pack retorna texto → agente
```

---

## G. Contrato Faltante para Symbol↔Chunk Links

### Lo que Necesita Existir

| Contrato | Descripción | Estado |
|----------|-------------|--------|
| **Symbol File Reference** | Mapping symbol → file_path (relativo a segment) | ⚠️ Existe en AST |
| **Chunk File Reference** | Mapping chunk → source_path | ✅ Existe |
| **Range Mapping** | symbol line range → chunk line range | ❌ No existe |
| **Versioned Pack ID** | SHA del pack para validar staleness | ❌ No existe |
| **Symbol ID Scheme** | Identificador estable para símbolos | ❌ No existe |

### Propuesta Mínima de endurecimiento

Para hacer viable el link, el pack debería incluir:

```json
{
  "schema_version": 2,  // Nuevo version
  "pack_id": "sha256_de_todos_los_archivos",
  "files_index": {
    "relative/path.py": {
      "sha256": "...",
      "symbols": [
        {"name": "Func", "kind": "function", "start_line": 10, "end_line": 20}
      ]
    }
  }
}
```

Pero esto **no existe hoy** y **no es necesario** para el objetivo de Graph.

---

## H. Veredicto Final

### Integración viable ya?

**NO - Requiere endurecimiento previo**

### Por qué no es viable actualmente

1. **Chunk IDs son efímeros** - basados en hash de contenido
2. **No hay line ranges** - chunks son whole_file, no segmentados
3. **No hay symbol→chunk mapping** - sistemas completamente desconectados
4. **Pack rebuild destruye IDs** - cualquier cambio regenera todo

### Lo que SÍ puede hacerse

| Enfoque | Evaluación |
|---------|-----------|
| Graph como señal de ranking para ctx search | ✅ Seguro - usa términos, no IDs |
| Graph sugiriendo source_paths para ctx get | ⚠️ Requiere normalización |
| Graph reemplazando ctx search internamente | ❌ No - rompe separación |
| Graph generando texto para prompt | ❌ No - rompe paradigma PCC |

### Próximo paso exacto

1. **NO intentar symbol↔chunk linking** - el contrato no existe
2. **Graph debe operar en capa de señales**, no de recuperación de texto
3. **Usar Graph para mejorar ctx search ranking**:
   - Graph retorna: `{symbol: "X", related_terms: ["A", "B"]}`
   - ctx search usa esos términos para mejorar hits
4. **Dejar PCC como única fuente de texto** - Graph solo informa, no provee

---

## I. Recomendación de Arquitectura

```
                    ┌─────────────────────────────────────┐
                    │           AGENTE                    │
                    │   (pide contexto sobre "X")         │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │              PCC                    │
                    │   (decide qué invocar)              │
                    │   - ctx search si necesita búsqueda │
                    │   - ctx get si tiene chunk_ids     │
                    └──────────────┬──────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼───────┐       ┌─────────▼─────────┐    ┌──────────▼─────────┐
│   Context    │       │      Graph       │    │       AST         │
│    Pack      │       │    (señal)      │    │   (símbolos)      │
│  (texto)     │       │                  │    │                   │
│              │       │  Ranking hints:  │    │  source_paths    │
│ ctx search → │       │  - "usa X"       │    │  line ranges     │
│ ctx get    ← │       │  - "relacionado" │    │                   │
└──────────────┘       │  - "impacta Y"    │    └───────────────────┘
                       └──────────────────┘
```

**PCC consulta Graph** → Graph retorna señales → **PCC decide** → PCC invoca Context Pack
