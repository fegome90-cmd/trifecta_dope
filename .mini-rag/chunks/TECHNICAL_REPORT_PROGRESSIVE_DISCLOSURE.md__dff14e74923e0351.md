### 4.3 Implementación Implícita

El modo `raw` con `budget_token_est` alto podría considerarse una forma de L2:

```python
# Equivalente a L2 "de facto"
ctx.get(ids=["chunk_id"], mode="raw", budget_token_est=10000)
```

Sin embargo, esto no es una "capa" arquitectónica, solo un parámetro de configuración.

---
