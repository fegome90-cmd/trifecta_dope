#### Hotset Cache (Memoria)

**Solo los 5 archivos activos**:
```python
class HotsetCache:
    def __init__(self):
        self.cache = {}  # file_path -> CachedFile

    def update(self, file_path: Path):
        """Update cache when file changes."""
        content = file_path.read_text()

        self.cache[str(file_path)] = {
            "text": content,
            "ast": parse_ast(content),
            "symbols": extract_symbols(content),
            "skeleton": generate_skeleton(content),
            "mtime": file_path.stat().st_mtime,
            "hash": hashlib.sha256(content.encode()).hexdigest()
        }
```
