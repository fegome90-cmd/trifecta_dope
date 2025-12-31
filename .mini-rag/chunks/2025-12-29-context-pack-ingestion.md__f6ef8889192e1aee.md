### 3. Stable IDs via Normalization

**Problem**: Sequential IDs (`skill:0001`) break on insert. Raw hash changes on whitespace.

**Solution**: Normalized components + hash:

```python
def normalize_title_path(path: list[str]) -> str:
    return "\x1f".join(p.strip().lower().collapse_spaces() for p in path)

def generate_chunk_id(doc: str, title_path: list[str], text: str) -> str:
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    seed = f"{doc}\n{normalize_title_path(title_path)}\n{text_hash}"
    return hashlib.sha1(seed.encode()).hexdigest()[:10]

# Result: "skill:a1b2c3d4e5"
```
