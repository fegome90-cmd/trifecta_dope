#### 1. Skeletonizer Automático (L0/L1)

**Vista compacta de estructura**:
```txt
[file: src/ingest_trifecta.py]
- def build_pack(md_paths, out_path="context_pack.json") -> str
- def chunk_by_headings(doc_id: str, md: str, max_chars: int=6000) -> List[Chunk]
- class Chunk(id: str, title_path: List[str], text: str, ...)
- SCHEMA_VERSION = 1
```

**Uso**: Digest real (estructura sin cuerpos). Siempre en L0.
