## 3. Configuracion

Archivo principal: `.mini-rag/config.yaml`

Puntos clave:
- `docs_glob`: apunta a `.mini-rag/chunks/**/*.md` y PDFs en `knowledge/`.
- `chunking`: reglas de chunking (seccion + fallback + overlap bajo).
- `retrieval`: `similarity_threshold` y `top_k_default`.
- `source_globs`: define que documentos se indexan.
- `exclude_globs`: excluye benchmarks o docs de referencia.
