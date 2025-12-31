### Preview

```python
def preview(text: str, max_chars: int = 180) -> str:
    """Generate one-line preview of chunk content."""
    # Collapse all whitespace to single space
    one_liner = re.sub(r"\s+", " ", text.strip())
    return one_liner[:max_chars] + ("…" if len(one_liner) > max_chars else "")
```

**Ejemplo**:

```python
text = """## Commands

- pytest -v
- ruff check
"""

preview(text, 50)
# → "## Commands - pytest -v - ruff check"
```
