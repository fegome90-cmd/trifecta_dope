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
