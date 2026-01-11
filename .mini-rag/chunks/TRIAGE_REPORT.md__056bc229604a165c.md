### Bucket 1: PR2 Fixture Error (10 errors)

```
tests/unit/test_pr2_integration.py:53
TypeError: SymbolResolver.__init__() missing 1 required positional argument: 'root'
```

**Fix**:
```python
# src/application/symbol_selector.py
def __init__(self, builder: Any, root: Path = None):
```

**ROI**: 10 errors → 0 errors

---
