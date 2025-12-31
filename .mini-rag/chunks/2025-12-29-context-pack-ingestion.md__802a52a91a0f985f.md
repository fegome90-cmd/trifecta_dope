### 4. Preview Generation

```python
def preview(text: str, max_chars: int = 180) -> str:
    one_liner = re.sub(r"\s+", " ", text.strip())
    return one_liner[:max_chars] + ("…" if len(one_liner) > max_chars else "")
```
