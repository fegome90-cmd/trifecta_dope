### Type Safety en SymbolQuery

La clase `SymbolQuery` en `src/application/symbol_selector.py` implementa dos propiedades type-safe para manipular URIs de símbolos:

**1. `raw` property**: Retorna el URI completo del símbolo.
```python
from src.application.symbol_selector import SymbolQuery

# Con URI cacheado
query = SymbolQuery("mod", "foo.bar", None, "sym://python/mod/foo.bar")
assert query.raw == "sym://python/mod/foo.bar"

# Reconstrucción automática
query2 = SymbolQuery("type", "foo.bar", "MyClass")
assert query2.raw == "sym://python/type/foo.bar#MyClass"
```

**2. `qualified_name` property**: Retorna el nombre calificado (dot-separated).
```python
# Para módulos (sin member)
query = SymbolQuery("mod", "foo.bar", None)
assert query.qualified_name == "foo.bar"

# Para tipos (con member)
query2 = SymbolQuery("type", "foo.bar", "MyClass")
assert query2.qualified_name == "foo.bar.MyClass"
```
