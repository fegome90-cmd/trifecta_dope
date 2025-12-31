# Mini-RAG Manual de Uso

Mini-RAG es una herramienta de desarrollo para consultar documentacion del CLI. No forma parte del paradigma Trifecta en runtime.

## 1. Requisitos

- Python 3.12+
- `uv` instalado
- Repo local de Mini-RAG en `~/Developer/Minirag`

## 2. Setup del entorno

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv sync
source .venv/bin/activate
python ~/Developer/Minirag/scripts/install_improved.py --source ~/Developer/Minirag
```

Notas:
- Si falta pip en el venv: `python -m ensurepip --upgrade`.
- Si el script falla, revisa `~/Developer/Minirag/INSTALLATION_GUIDE.md`.

## 3. Configuracion

Archivo principal: `.mini-rag/config.yaml`

Puntos clave:
- `docs_glob`: apunta a `.mini-rag/chunks/**/*.md` y PDFs en `knowledge/`.
- `chunking`: reglas de chunking (seccion + fallback + overlap bajo).
- `retrieval`: `similarity_threshold` y `top_k_default`.
- `source_globs`: define que documentos se indexan.
- `exclude_globs`: excluye benchmarks o docs de referencia.

## 4. Chunking (mejoras aplicadas)

Chunker local: `scripts/minirag_chunker.py`

Caracteristicas:
- Markdown-aware (headings y fences)
- Normalizacion ligera (frontmatter, whitespace)
- Deduplicacion por hash
- Manifest de chunks

Generar chunks:

```bash
python scripts/minirag_chunker.py
```

## 5. Indexar

```bash
make minirag-index
```

Esto usa `.mini-rag/chunks/**/*.md` y PDFs definidos en config.

## 6. Consultar

```bash
make minirag-query MINIRAG_QUERY="ctx search"
```

Opcional (JSON):

```bash
source .venv/bin/activate
mini-rag query "ctx search" --json
```

## 7. Evaluacion y Bench

Directorio: `minirag-eval/`

Estructura:
- `minirag-eval/queries/` sets de queries
- `minirag-eval/specs/` criterios de evaluacion
- `minirag-eval/results/` resultados (no se versionan)
- `minirag-eval/run_bench.sh` runner
- `minirag-eval/summarize_results.py` resumen

Ejemplo:

```bash
bash minirag-eval/run_bench.sh lsp_ast_positive
python minirag-eval/summarize_results.py
```

## 8. Troubleshooting

### 8.1 mini-rag no encontrado

Reinstala:

```bash
source .venv/bin/activate
python ~/Developer/Minirag/scripts/install_improved.py --source ~/Developer/Minirag
```

### 8.2 Error de pip en venv

```bash
source .venv/bin/activate
python -m ensurepip --upgrade
```

### 8.3 Index no cambia despues de editar docs

```bash
python scripts/minirag_chunker.py
make minirag-index
```

### 8.4 Resultados irrelevantes

- Baja `retrieval.similarity_threshold` o sube `top_k_default`.
- Ajusta `source_globs` y `exclude_globs`.
- Revisa `minirag-eval/specs/` para calibrar.

## 9. Comandos utiles

```bash
make minirag-help
make minirag-index
make minirag-query MINIRAG_QUERY="..."
```

## 10. Registro de cambios

- Guia rapida: `readme_minirag.md`
- Evaluacion: `docs/testing/minirag_eval_log.md`
- Planes: `docs/plans/2025-12-31-minirag-chunker-plan.md`
