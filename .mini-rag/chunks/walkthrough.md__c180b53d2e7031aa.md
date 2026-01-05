### Configuración Mypy

El proyecto usa `mypy` en modo estricto (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.12"
strict = true
```

Esto habilita checks estrictos incluyendo:
- DisallowUntypedDefs
- DisallowIncompleteDefs
- CheckUntypedDefs
- NoAnyImport

---
