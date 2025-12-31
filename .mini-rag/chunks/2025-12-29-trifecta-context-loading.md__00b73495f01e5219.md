#### 2. Node-Get: Entregar Solo el Nodo Requerido (L2)

**En vez de archivo completo**:
```python
# Agente pide: "¿cómo calcula token_est?"
ctx.get_symbol(
    symbol_id="ingest_trifecta.py::estimate_tokens_rough",
    mode="node",  # Solo la función
    budget=300
)

# Devuelve:
# - Definición de función (20 líneas)
# - Dependencias directas (helpers usados)
# - Docstring
```

**Progressive disclosure real**: Solo lo necesario.
