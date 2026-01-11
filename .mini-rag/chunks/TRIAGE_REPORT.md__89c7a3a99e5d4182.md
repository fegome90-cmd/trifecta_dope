### Bucket 4: CLI Create Naming (4 failures)

```
tests/unit/test_cli_create_naming.py:27: AssertionError: Create failed: assert 2 == 0
```

**Root cause**: Tests usan `--segment` y `--path` args que no existen en CLI actual (usa `-s`).

**Fix**: Ajustar tests a usar args correctos.

**ROI**: 4 failures

---
