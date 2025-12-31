### Alta Prioridad

1. **Improve Ranking**
   ```python
   # Actual: todos 0.50
   # Propuesto: TF-IDF o BM25
   score = (term_freq_in_doc / max_freq) * log(total_docs / docs_with_term)
   ```
   **Impacto**: Fewer queries needed to find relevant chunk

2. **Deduplication in Index**
   ```python
   # Detectar chunks duplicados antes de indexar
   chunk_hashes = {}
   for chunk in chunks:
       hash = sha256(chunk.text)
       if hash not in chunk_hashes:
           index.append(chunk)
   ```
   **Impacto**: Reduce pack size by ~10-15%

3. **Fragment Large Docs**
   ```python
   # README.md (12.2K chars) → 3 chunks
   # Umbral: 4K chars por chunk
   if len(chunk.text) > 4000:
       split_by_h2_headers()
   ```
   **Impacto**: Better targeting, reduce avg chunk size to ~500 tokens
