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
