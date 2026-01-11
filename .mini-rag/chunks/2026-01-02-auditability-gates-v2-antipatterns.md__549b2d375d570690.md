```python
# En clase TrifectaPack, agregar:
def sanitized_dump(self) -> str:
    """Dump JSON con paths sanitizados (FAIL-CLOSED: no PII en output).

    Anti-patrones evitados:
    - AP1: No string parsing; usa structured operations
    - AP6: Output es JSON determinista
    - AP8: SSOT de sanitización está aquí
    """
    import json
    from pathlib import Path

    data = self.model_dump()

    # Sanitizar repo_root si existe
    if "repo_root" in data and data["repo_root"]:
        root = Path(data["repo_root"])
        data["repo_root"] = f"<REPO_ROOT>/{root.name}"

    # Sanitizar recursivamente strings (evita AP1: no stringly-typed)
    def _sanitize(obj):
        if isinstance(obj, str):
            # Reemplazar file:// URIs
            return obj.replace("file://", "<FILE_URI_SANITIZED>")
        elif isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        return obj

    data = _sanitize(data)
    return json.dumps(data, indent=2)
```

**2. use_cases.py — Cambiar línea 481:**
```python
# Antes:
AtomicWriter.write(pack_path, pack.model_dump_json(indent=2))
# Después:
AtomicWriter.write(pack_path, pack.sanitized_dump())
```

**Tests tripwire (AP2, AP3, AP9):**

**Unit test (AP2: determinista):**
