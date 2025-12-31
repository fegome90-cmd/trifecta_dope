#### 3. Diagnostics como Gatillo de Contexto

**Oro para debugging**:
```python
# Error en file A
diagnostics = lsp.diagnostics("src/ingest.py")
# [{"line": 45, "message": "KeyError: 'heading_level'", ...}]

# Automáticamente pedir:
# - Rango del error
# - Dependencias inmediatas
# - Símbolos relacionados

# Agente no adivina qué leer
```
