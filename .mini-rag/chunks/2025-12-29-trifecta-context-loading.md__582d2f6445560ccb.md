#### 4. IDs Estables Basados en Símbolo

**No usar chunk #**:
```python
# ❌ Malo: "chunk-005" (se rompe al editar)
# ✅ Bueno: "file::symbol::range" o hash de eso
id = f"{file_path}::{qualified_name}::{start_byte}-{end_byte}"
# Ejemplo: "src/ingest.py::build_pack::1234-5678"
```

**Beneficio**: Editas arriba, el símbolo sigue apuntando bien.

---
