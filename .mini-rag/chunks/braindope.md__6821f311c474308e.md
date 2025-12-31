# 9) CLI Esperado

```bash
# Crear nueva trifecta
uv run python scripts/trifecta.py create \
    --segment eval-harness \
    --path eval/eval-harness/ \
    --scan-docs eval/docs/

# Validar trifecta existente
uv run python scripts/trifecta.py validate --path eval/eval-harness/

# Actualizar solo prime (re-escanea docs)
uv run python scripts/trifecta.py refresh-prime --path eval/eval-harness/
```

---
