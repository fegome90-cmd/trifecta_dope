### Implementación

```python
def normalize_markdown(md: str) -> str:
    """Normalize markdown for consistent processing."""
    md = md.replace("\r\n", "\n").strip()
    # Collapse multiple blank lines to double newline
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md + "\n" if md else ""
```
