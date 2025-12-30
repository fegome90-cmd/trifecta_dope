# Context Pack Implementation - Foundational Design Document

**Date**: 2025-12-29 (Original Design)
**Version**: 1.0 (Foundational Spec)
**Status**: 📚 **Historical Reference & Knowledge Base**

---

> **📌 About This Document**
>
> Este es el **documento de diseño original** donde nació la arquitectura del Context Pack.
> Contiene el conocimiento fundacional del sistema de 3 capas (Digest/Index/Chunks) y
> la lógica fence-aware que aún se usa en producción.
>
> **Evolución del Sistema**:
> - **Original**: `scripts/ingest_trifecta.py` (referenciado aquí)
> - **Actual**: `uv run trifecta ctx build` (CLI en `src/infrastructure/cli.py`)
> - **Lógica Core**: Ahora en `src/application/use_cases.py` (Clean Architecture)
>
> **Por qué mantener este documento**:
> - Explica el "por qué" detrás de decisiones de diseño
> - Documenta algoritmos de chunking, scoring y normalización
> - Referencia educativa para entender el sistema completo
> - Fuente de ideas para futuras mejoras (ej: SQLite Phase 2)
>
> **Para comandos actuales**, ver: [README.md](../../README.md) o `uv run trifecta --help`

---

## Overview

El Context Pack es un sistema de 3 capas para ingestión token-optimizada de documentación Markdown hacia LLMs. Permite cargar contexto eficiente sin inyectar textos completos en cada prompt.

```
┌─────────────────────────────────────────────────────────────┐
│  Context Pack (context_pack.json)                           │
├─────────────────────────────────────────────────────────────┤
│  Digest    → Siempre en prompt (~10-30 líneas)              │
│  Index     → Siempre en prompt (referencias de chunks)       │
│  Chunks    → Bajo demanda vía tool (texto completo)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Arquitectura

### Flujo de Datos

```
Markdown Files
       ↓
   Normalize
       ↓
Fence-Aware Chunking
       ↓
  Generate IDs
       ↓
Score for Digest
       ↓
Build Index
       ↓
context_pack.json
```

### Componentes Principales

| Componente | Responsabilidad |
|------------|-----------------|
| `normalize_markdown()` | Estandarizar formato (CRLF → LF, collapse blank lines) |
| `chunk_by_headings_fence_aware()` | Dividir en chunks respetando code fences |
| `generate_chunk_id()` | Crear IDs estables via hash |
| `score_chunk()` | Puntuar chunks para digest |
| `ContextPackBuilder` | Orquestar generación completa |

---

## Paso 1: Normalización de Markdown

### Objetivo
Convertir markdown en formato consistente para procesamiento.

### Implementación

```python
def normalize_markdown(md: str) -> str:
    """Normalize markdown for consistent processing."""
    md = md.replace("\r\n", "\n").strip()
    # Collapse multiple blank lines to double newline
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md + "\n" if md else ""
```

### Qué hace:

1. **CRLF → LF**: Convierte terminaciones Windows a Unix
2. **Strip**: Elimina whitespace al inicio/final
3. **Collapse blank lines**: `\n\n\n+` → `\n\n`
4. **Trailing newline**: Asegura `\n` al final

### Ejemplo

```python
# Input
"Line 1\r\nLine 2\n\n\n\nLine 3   "

# Output
"Line 1\nLine 2\n\nLine 3\n"
```

---

## Paso 2: Normalización de Title Path

### Objetivo
Crear rutas de títulos consistentes para generación de IDs estables.

### Implementación

```python
def normalize_title_path(path: list[str]) -> str:
    """
    Normalize title path for stable ID generation.
    Uses ASCII 0x1F (unit separator) to join titles.
    """
    normalized = []
    for title in path:
        # Trim and collapse whitespace
        title = title.strip().lower()
        title = re.sub(r"\s+", " ", title)
        normalized.append(title)
    return "\x1f".join(normalized)
```

### Por qué es importante

Si no normalizas, estos títulos generarían IDs **distintos** para el mismo contenido lógico:

```python
# Sin normalizar (MAL)
["Core Rules", "  Sync   First"] → "Core Rules\x1f  Sync   First"
["Core Rules", "Sync First"]     → "Core Rules\x1fSync First"

# Con normalizar (BIEN)
["Core Rules", "  Sync   First"] → "core rules\x1fsync first"
["Core Rules", "Sync First"]     → "core rules\x1fsync first"
```

---

## Paso 3: Chunking Fence-Aware

### Objetivo
Dividir markdown en chunks usando headings como separadores, **respetando bloques de código**.

### Problema

Si ignoramos code fences, headings dentro de ``` bloques crearían chunks incorrectos:

```markdown
## Example Code

```python
def function():
    # Este heading NO debe crear un chunk
    pass
```

## After Fence
```

### Solución: State Machine

```python
def chunk_by_headings_fence_aware(
    doc_id: str,
    md: str,
    max_chars: int = 6000
) -> list[dict]:
    """
    Split markdown into chunks using headings, respecting code fences.
    """
    lines = md.splitlines()
    chunks = []

    # Estado actual
    title = "INTRO"
    title_path: list[str] = []
    level = 0
    start_line = 0
    buf: list[str] = []
    in_fence = False  # ← State machine flag

    def flush(end_line: int) -> None:
        """Flush accumulated buffer as a chunk."""
        nonlocal title, level, start_line, buf
        if buf:
            text = "\n".join(buf).strip()
            if text:
                chunks.append({
                    "title": title,
                    "title_path": title_path.copy(),
                    "level": level,
                    "text": text,
                    "start_line": start_line + 1,
                    "end_line": end_line,
                })
            buf = []
            start_line = end_line + 1

    for i, line in enumerate(lines):
        # 1. Detectar toggle de fence
        fence_match = FENCE_RE.match(line)
        if fence_match:
            in_fence = not in_fence  # Toggle estado
            buf.append(line)
            continue

        # 2. Solo procesar headings fuera de fences
        heading_match = HEADING_RE.match(line)
        if heading_match and not in_fence:
            flush(i)  # Guardar chunk anterior

            # Iniciar nuevo chunk
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            title_path = title_path[:level - 1] + [title]
            start_line = i
            buf = [line]
        else:
            buf.append(line)

    flush(len(lines))  # Flush final chunk

    # ... (handle oversized chunks with paragraph fallback)

    return final_chunks
```

### Máquina de Estados

```
┌─────────────┐  ``` o ~~~  ┌──────────────┐
│  in_fence   │ ──────────→ │  in_fence    │
│   = False   │             │   = True     │
└─────────────┘             └──────────────┘
      ↑                           │
      │       ``` o ~~~            │
      └───────────────────────────┘
```

**Regla**: Si `in_fence == True`, ignorar headings.

---

## Paso 4: Generación de IDs Estables

### Objetivo
Crear IDs deterministas que no cambien entre runs.

### Fórmula

```python
def generate_chunk_id(doc: str, title_path: list[str], text: str) -> str:
    """
    Generate stable chunk ID from normalized components.
    Format: {doc}:{10-char-hash}
    """
    # 1. Hash del texto (SHA-256 para evitar colisiones)
    text_hash = sha256_text(text)

    # 2. Seed normalizado
    seed = f"{doc}\n{normalize_title_path(title_path)}\n{text_hash}"

    # 3. Hash del seed (SHA-1 truncado a 10 chars)
    chunk_hash = hashlib.sha1(seed.encode()).hexdigest()[:10]

    return f"{doc}:{chunk_hash}"
```

### Propiedades de Estabilidad

| Cambio en contenido | ¿Cambia ID? | Por qué |
|---------------------|-------------|---------|
| Mismo texto, mismo título | ❌ No | Mismo seed → mismo hash |
| Texto modificado | ✅ Sí | `text_hash` cambia |
| Whitespace en título | ❌ No | `normalize_title_path()` elimina |
| Case en título | ❌ No | `lower()` en normalización |
| Cambio en otro doc | ❌ No | ID incluye `doc` como prefijo |

### Ejemplo

```python
# Chunk 1
id1 = generate_chunk_id("skill", ["Core Rules"], "Test content")
# → "skill:a1b2c3d4e5"

# Mismo contenido, mismo ID
id2 = generate_chunk_id("skill", ["Core Rules"], "Test content")
# → "skill:a1b2c3d4e5"

# Contenido diferente, ID diferente
id3 = generate_chunk_id("skill", ["Core Rules"], "Different content")
# → "skill:f6e7d8c9b0"

# Distinto documento, IDs independientes
id4 = generate_chunk_id("agent", ["Core Rules"], "Test content")
# → "agent:a1b2c3d4e5" (mismo hash, distinto doc)
```

---

## Paso 5: Digest por Scoring

### Objetivo
Seleccionar los chunks más relevantes para el digest (máximo 2 por doc, 1200 chars total).

### Sistema de Scoring

```python
def score_chunk(title: str, level: int, text: str) -> int:
    """
    Score a chunk for digest inclusion.
    Higher score = more relevant.
    """
    score = 0
    title_lower = title.lower()

    # +3 puntos: Keywords relevantes
    relevant_keywords = [
        "core", "rules", "workflow", "commands",
        "usage", "setup", "api", "architecture",
        "critical", "mandatory", "protocol"
    ]
    if any(kw in title_lower for kw in relevant_keywords):
        score += 3

    # +2 puntos: Headings de alto nivel (## o #)
    if level <= 2:
        score += 2

    # -2 puntos: Overview/Intro vacío (fluff)
    fluff_keywords = ["overview", "intro", "introduction"]
    if any(kw in title_lower for kw in fluff_keywords) and len(text) < 300:
        score -= 2

    return score
```

### Algoritmo de Selección

```python
def build_digest(self, doc_id: str, chunks: list[dict]) -> dict:
    """Build deterministic digest entry."""
    # 1. Scorear todos los chunks
    scored = []
    for chunk in chunks:
        title = chunk["title_path"][-1] if chunk["title_path"] else "Introduction"
        score = score_chunk(title, chunk["heading_level"], chunk["text"])
        scored.append((score, chunk))

    # 2. Ordenar por score (descending)
    scored.sort(key=lambda x: x[0], reverse=True)

    # 3. Tomar top-2, max 1200 chars
    selected_chunks = []
    total_chars = 0
    for score, chunk in scored[:2]:
        if total_chars + chunk["char_count"] > 1200:
            break
        selected_chunks.append(chunk)
        total_chars += chunk["char_count"]

    # 4. Construir summary
    titles = []
    for c in selected_chunks:
        title = " → ".join(c["title_path"]) if c["title_path"] else "Introduction"
        titles.append(title)

    summary = " | ".join(titles) if titles else "No content"

    return {
        "doc": doc_id,
        "summary": summary,
        "source_chunk_ids": [c["id"] for c in selected_chunks],
    }
```

### Ejemplo de Scoring

| Chunk Title | Level | Keywords | Score |
|-------------|-------|----------|-------|
| "Core Rules" | 2 | "core", "rules" | 3+2=5 |
| "Overview" | 2 | "overview" (<300 chars) | -2 |
| "Commands" | 2 | "commands" | 3+2=5 |
| "Deep Nested Section" | 4 | - | 0 |

**Resultado**: Digest selecciona "Core Rules" y "Commands" (score 5), omite "Overview" (score -2).

---

## Paso 6: Preview y Token Estimation

### Preview

```python
def preview(text: str, max_chars: int = 180) -> str:
    """Generate one-line preview of chunk content."""
    # Collapse all whitespace to single space
    one_liner = re.sub(r"\s+", " ", text.strip())
    return one_liner[:max_chars] + ("…" if len(one_liner) > max_chars else "")
```

**Ejemplo**:

```python
text = """## Commands

- pytest -v
- ruff check
"""

preview(text, 50)
# → "## Commands - pytest -v - ruff check"
```

### Token Estimation

```python
def estimate_tokens(text: str) -> int:
    """Rough token estimation: 1 token ≈ 4 characters."""
    return len(text) // 4
```

> **Nota**: Estimación aproximada. Para tokens exactos, usar tokenizer del modelo.

---

## Paso 7: Context Pack Builder

### Clase Principal

```python
class ContextPackBuilder:
    """Builds token-optimized Context Pack from markdown files."""

    def __init__(self, segment: str, repo_root: Path):
        self.segment = segment
        self.repo_root = repo_root
        self.segment_path = repo_root / segment

    def build(self, output_path: Path | None = None) -> dict:
        """
        Build complete Context Pack.
        """
        # 1. Encontrar archivos markdown
        md_files = self.find_markdown_files()

        # 2. Procesar cada documento
        docs = []
        all_chunks = []
        for path in md_files:
            doc_id, content = self.load_document(path)
            chunks = self.build_chunks(doc_id, content, path)

            docs.append({
                "doc": doc_id,
                "file": path.name,
                "sha256": sha256_text(content),
                "chunk_count": len(chunks),
                "total_chars": len(content),
            })
            all_chunks.extend(chunks)

        # 3. Construir índice
        index = []
        for chunk in all_chunks:
            title = " → ".join(chunk["title_path"]) if chunk["title_path"] else "Introduction"
            index.append({
                "id": chunk["id"],
                "doc": chunk["doc"],
                "title_path": chunk["title_path"],
                "preview": preview(chunk["text"]),
                "token_est": estimate_tokens(chunk["text"]),
                # ... más metadata
            })

        # 4. Construir digest
        digest = []
        for doc in docs:
            doc_chunks = [c for c in all_chunks if c["doc"] == doc["doc"]]
            if doc_chunks:
                digest.append(self.build_digest(doc["doc"], doc_chunks))

        # 5. Ensamblar pack
        pack = {
            "schema_version": 1,
            "segment": self.segment,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": "0.1.0",
            "source_files": [...] (Diseño Original)

> **⚠️ Comandos Actualizados**:
> 
> El diseño original usaba `scripts/ingest_trifecta.py`. En v1.0+, usa:
> ```bash
> # Generar context pack
> uv run trifecta ctx build --segment .
> 
> # Sincronizar (build + validate)
> uv run trifecta ctx sync --segment .
> 
> # Buscar en el pack
> uv run trifecta ctx search --segment . --query "tema"
> 
> # Obtener chunks específicos
> uv run trifecta ctx get --segment . --ids "chunk_id" --mode raw
> ```
>
> El código siguiente documenta la **arquitectura original** (referencia educativa):

```python
def main():
    parser = argparse.ArgumentParser(
        description="Generate token-optimized Context Pack from Trifecta documentation",
        epilog="""Examples:
  python ingest_trifecta.py --segment debug_terminal
  python ingest_trifecta.py --segment hemdov --repo-root /path/to/projects
  python ingest_trifecta.py --segment eval --output custom/pack.json --dry-run""",
    )
    parser.add_argument("--segment", "-s", required=True)
    parser.add_argument("--repo-root", "-r", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--force", "-f", action="store_true")

    args = parser.parse_args()

    # Validar segment existe
    builder = ContextPackBuilder(args.segment, args.repo_root)
    if not builder.segment_path.exists():
        raise ValueError(f"Segment path does not exist: {builder.segment_path}")

    # Generar pack
    pack = builder.build(args.output if not args.dry_run else None)

    # Mostrar resultado
    if args.dry_run:
        print(f"[dry-run] Would generate Context Pack: ...")
    else:
        print(f"[ok] Context Pack generated: ...")

    if args.verbose:
        print(f"\n[verbose] Digest entries:")
        for d in pack["digest"]:
            print(f"  - {d['doc']}: {d['summary']}")
```

### Uso (Diseño Original → Comandos Actuales)

```bash
# DISEÑO ORIGINAL (scripts/ingest_trifecta.py)
# ─────────────────────────────────────────────────────────────────

# Básico
python scripts/ingest_trifecta.py --segment debug_terminal

# Con repo root personalizado
python scripts/ingest_trifecta.py --segment hemdov --repo-root /path/to/projects

# Dry-run + verbose (preview)
python scripts/ingest_trifecta.py --segment debug_terminal --dry-run --verbose

# Output personalizado
python scripts/ingest_trifecta.py --segment eval --output custom/pack.json


# COMANDOS ACTUALES (v1.0+ CLI)
# ─────────────────────────────────────────────────────────────────

# Generar pack (equivalente a ingest básico)
uv run trifecta ctx build --segment .

# Sincronizar (build + validate automático)
uv run trifecta ctx sync --segment .

# Validar pack existente
uv run trifecta ctx validate --segment .

# Buscar en pack (nuevo en v1.0)
uv run trifecta ctx search --segment . --query "core rules" --limit 5

# Ver estadísticas
uv run trifecta ctx stats --segment .

    if args.verbose:
        print(f"\n[verbose] Digest entries:")
        for d in pack["digest"]:
            print(f"  - {d['doc']}: {d['summary']}")
```

### Uso

```bash
# Básico
python scripts/ingest_trifecta.py --segment debug_terminal

# Con repo root personalizado
python scripts/ingest_trifecta.py --segment hemdov --repo-root /path/to/projects

# Dry-run + verbose (preview)
python scripts/ingest_trifecta.py --segment debug_terminal --dry-run --verbose

# Output personalizado
python scripts/ingest_trifecta.py --segment eval --output custom/pack.json
```

---

## Schema v1 Completo

```json
{
  "schema_version": 1,
  "segment": "debug_terminal",
  "created_at": "2025-12-29T15:55:14.431888+00:00",
  "generator_version": "0.1.0",
  "source_files": [
    {
      "path": "debug_terminal/skill.md",
      "sha256": "e9232d8d539fb1707b82f83ddb7f0e95b25ad0aa6183505b59c0f82619fce007",
      "mtime": 1767022643,
      "chars": 2172,
      "size": 2180
    }
  ],
  "chunking": {
    "method": "headings+paragraph_fallback+fence_aware",
    "max_chars": 6000
  },
  "docs": [
    {
      "doc": "skill",
      "file": "skill.md",
      "sha256": "c32e4060af63024c2a87467e918064ed08e3cb30fb5ca2f644f4b66739baed66",
      "chunk_count": 9,
      "total_chars": 2171
    }
  ],
  "digest": [
    {
      "doc": "skill",
      "summary": "Debug Terminal → Mandatory Onboarding | Debug Terminal → Instructions → CRITICAL PROTOCOL: History Persistence",
      "source_chunk_ids": ["skill:a1b2c3d4e5", "skill:f6e7d8c9b0"]
    }
  ],
  "index": [
    {
      "id": "skill:a1b2c3d4e5",
      "doc": "skill",
      "title_path": ["Debug Terminal"],
      "preview": "Debug Terminal 2.0 (DT2): observability cockpit...",
      "token_est": 45,
      "source_path": "debug_terminal/skill.md",
      "heading_level": 1,
      "char_count": 180,
      "line_count": 3,
      "start_line": 11,
      "end_line": 13
    }
  ],
  "chunks": [
    {
      "id": "skill:a1b2c3d4e5",
      "title_path": ["Debug Terminal"],
      "text": "## Debug Terminal\n\nDebug Terminal 2.0 (DT2): observability cockpit...",
      "source_path": "debug_terminal/skill.md",
      "heading_level": 1,
      "char_count": 180,
      "line_count": 3,
      "start_line": 11,
      "end_line": 13
# Diseño original:
$ python scripts/ingest_trifecta.py --segment debug_terminal

# Comando actual (v1.0+):
$ uv run trifecta ctx build --segment debug_terminal

# Output (ambos generan estructura similar):
  ]
}
```

---

## Testing

### Cobertura de Tests

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| Normalization | 3 | CRLF → LF, collapse blanks, title path |
| ID Stability | 4 | Deterministic, different doc, whitespace, case |
| Fence-Aware | 4 | Code blocks, state machine, hierarchy |
| Scoring | 4 | Keywords, level, penalties, negative |
| Preview | 3 | Collapse whitespace, truncate, ellipsis |
| Integration | 2 | Full build, stability across runs |
| Output | 1 | File written correctly |
| **Total** | **22** | |

### Ejemplo de Test

```python
def test_fence_aware_state_machine_toggle():
    """The in_fence state should toggle correctly."""
    sample = """# Intro

```python
# First block
def foo():
    pass
```

## Middle

```python
# Second block
## Inside fence should not split
x = 1
```

## End
"""
    chunks = chunk_by_headings_fence_aware("test", sample)
    chunk_titles = [c["title"] for c in chunks]

    # Should only have: Intro, Middle, End
    assert "Intro" in chunk_titles
    assert "Middle" in chunk_titles
    assert "End" in chunk_titles
    assert "Inside fence should not split" not in chunk_titles
```

---

## Métricas de Producción

### debug_terminal (Real)

```bash
$ python scripts/ingest_trifecta.py --segment debug_terminal
[ok] Context Pack generated:
    • 34 chunks
    • 5 digest entries
    • 34 index entries
    → /Users/felipe_gonzalez/Developer/agent_h/debug_terminal/_ctx/context_pack.json
```

### Digest Output
 - Ideas Avanzadas)

> **💡 Idea Original para Escalabilidad**
>
> Esta sección describe una **propuesta futura** para cuando el context pack crezca.
> Actualmente (v1.0), usamos JSON simple que funciona bien para <100 chunks.
> 
> **Estado actual**: JSON en `_ctx/context_pack.json`  
> **Roadmap**: SQLite cuando superemos ~200 chunks o necesitemos búsqueda compleja

Cuando el context pack crezca, migrar chunks a SQLite:

```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    doc TEXT,
    title_path TEXT,
    text TEXT,
    source_path TEXT,
    heading_level INTEGER,
    char_count INTEGER,
    line_count INTEGER,
    start_line INTEGER,
    end_line INTEGER
);

CREATE INDEX idx_chunks_doc ON chunks(doc);
CREATE INDEX idx_chunks_title_path ON chunks(title_path);

-- Futuro: Full-text search
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    id UNINDEXED,
    title_path,
    text,
    content='chunks',
    content_rowid='rowid'
);
```

**Beneficios**:
- Búsqueda O(1) por ID
- Soporte para miles de chunks sin degradación
- Full-text search con BM25 (mejor que grep)
- Query optimization automático
- Preparado para embedding vectors (futuro v2.0)

**Decisiones de Diseño a Tomar**:
- ¿Mantener JSON como fallback? (para portabilidad)
- ¿Migrar índice también a SQLite o solo chunks?
- ¿Usar SQLite en memoria para queries frecuentes?

**Referencias**:
- Ver `docs/research/braindope.md` para ideas de Progressive Disclosure
- Relacionado con v2.0 roadmap (embeddings + reranking
## Index (Available Sections)
{format_index(context_pack['index'])}

To get full content of any section, use: get_context(chunk_id)
"""
```

### Tool Runtime

```python
def get_context(chunk_id: str) -> str:
    """Get full text of a chunk by ID."""
    pack = load_json("context_pack.json")
    for chunk in pack["chunks"]:
        if chunk["id"] == chunk_id:
            return chunk["text"]
    raise ValueError(f"Chunk not found: {chunk_id}")
```

---

## Phase 2: SQLite (Futuro)

Cuando el context pack crezca, migrar chunks a SQLite:

```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    doc TEXT,
    title_path TEXT,
    text TEXT,
    source_path TEXT,
    heading_level INTEGER,
    char_count INTEGER,
    line_count INTEGER,
    start_line INTEGER,
    end_line INTEGER
);

CREATE INDEX idx_chunks_doc ON chunks(doc);
CREATE INDEX idx_chunks_title_path ON chunks(title_path);
```

**Beneficios**:
- Búsqueda O(1) por ID
- Soporte para miles de chunks
- Preparado para full-text search (BM25)
