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
