### D.3) Tests de privacy ausentes

**SCOOP propone** (sección 8):
```bash
uv run trifecta session query -s . --last 1 --format raw | \
  rg "/Users/|/home/" && exit 1 || exit 0
```

**PROBLEMA**: ❌ No hay test automatizado en `tests/`

**BLOCKER #7**: Crear `tests/acceptance/test_no_privacy_leaks.py`:
