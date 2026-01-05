### Rule #2: Relative Paths Only
```python
# ✅ DO THIS:
telemetry.event("ast.parse", {"file": "src/domain/models.py"}, ...)

# ❌ DON'T DO THIS:
telemetry.event("ast.parse", {"file": "/Users/alice/code/src/domain/models.py"}, ...)
```
