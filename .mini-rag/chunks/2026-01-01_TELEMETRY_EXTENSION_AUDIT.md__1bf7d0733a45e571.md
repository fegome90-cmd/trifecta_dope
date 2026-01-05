### N.3 Relative Path Redaction

Always use `Path.relative_to()` or fallback to `.name` (filename only) for telemetry:
```python
try:
    rel = path.relative_to(segment_root)
except ValueError:
    rel = path.name
telemetry.event(..., {"file": str(rel)}, ...)
```
