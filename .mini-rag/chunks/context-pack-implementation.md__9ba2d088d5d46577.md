### Por qué es importante

Si no normalizas, estos títulos generarían IDs **distintos** para el mismo contenido lógico:

```python
# Sin normalizar (MAL)
["Core Rules", "  Sync   First"] → "Core Rules\x1f  Sync   First"
["Core Rules", "Sync First"]     → "Core Rules\x1fSync First"

# Con normalizar (BIEN)
["Core Rules", "  Sync   First"] → "core rules\x1fsync first"
["Core Rules", "Sync First"]     → "core rules\x1fsync first"
```

---
