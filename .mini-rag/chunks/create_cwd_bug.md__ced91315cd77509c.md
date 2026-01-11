## Workaround
Manually create `_ctx/` structure with correct naming:
```python
ctx_dir = segment / "_ctx"
ctx_dir.mkdir()
prime_file = ctx_dir / f"prime_{segment.name}.md"
prime_file.write_text(...)
```
