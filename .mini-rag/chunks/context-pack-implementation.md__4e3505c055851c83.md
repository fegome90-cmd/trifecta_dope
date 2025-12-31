### Implementación

```python
def normalize_title_path(path: list[str]) -> str:
    """
    Normalize title path for stable ID generation.
    Uses ASCII 0x1F (unit separator) to join titles.
    """
    normalized = []
    for title in path:
        # Trim and collapse whitespace
        title = title.strip().lower()
        title = re.sub(r"\s+", " ", title)
        normalized.append(title)
    return "\x1f".join(normalized)
```
