### Fase 4: Recuperación (Get Cycle)

```bash
Command: uv run trifecta ctx get \
  --segment . \
  --ids "agent:39151e4814" \
  --mode raw \
  --budget-token-est 900

Status: SUCCESS
Chunks Retrieved: 1
Tokens Delivered: 726
Budget Remaining: 174 tokens
Time: <1s
```

**Content Fragment**:
```markdown
## Gates (Comandos de Verificación)

| Gate | Comando | Propósito |
|------|---------|-----------|
| **Unit** | `uv run pytest tests/unit/ -v` | Lógica interna |
| **Integración** | `uv run pytest tests/test_use_cases.py -v` | Flujos CLI/UseCases |
...
```

---
