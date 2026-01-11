```python
# En clase TrifectaPack, agregar:
def sanitized_dump(self) -> str:
    """Dump JSON con paths sanitizados (sin PII)."""
    data = self.model_dump()
    if "repo_root" in data and data["repo_root"]:
        # Reemplazar path absoluto con placeholder relativo
        root = Path(data["repo_root"])
        data["repo_root"] = f"<REPO_ROOT>/{root.name}"
    # Sanitizar cualquier string con file:// URI
    def sanitize_strings(obj):
        if isinstance(obj, str):
            return obj.replace("file://", "<FILE_URI_SANITIZED>")
        elif isinstance(obj, dict):
            return {k: sanitize_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_strings(item) for item in obj]
        return obj
    data = sanitize_strings(data)
    return json.dumps(data, indent=2)
```

**2. Cambiar use_cases.py línea 481:**
```python
# Antes:
AtomicWriter.write(pack_path, pack.model_dump_json(indent=2))
# Después:
AtomicWriter.write(pack_path, pack.sanitized_dump())
```

**Test tripwire (dos niveles):**

**Unit test:**
