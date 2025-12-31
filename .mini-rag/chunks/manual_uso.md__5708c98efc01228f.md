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
