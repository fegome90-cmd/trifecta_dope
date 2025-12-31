### Niveles de Detalle

**L0 (siempre en prompt)**: `digest + index` (muy corto)
```json
{
  "segment": "debug-terminal",
  "digest": "Debug Terminal: tmux cockpit + sanitization. 3 docs: skill, agent, session.",
  "index": [
    {"id": "skill-md-whole", "title": "skill.md", "token_est": 625},
    {"id": "agent-md-whole", "title": "agent.md", "token_est": 800}
  ]
}
```

**L1 (bajo demanda)**: `excerpt` de chunks relevantes
```python
ctx.get(
    ids=["skill-md-whole"],
    mode="excerpt",  # Primeras 10 líneas
    budget_token_est=300
)
```

**L2 (solo si necesario)**: `raw` del chunk completo
```python
ctx.get(
    ids=["skill-md-whole"],
    mode="raw",  # Texto completo
    budget_token_est=900
)
```

**L3 (opcional futuro)**: `skeleton` (solo headers/comandos/ejemplos)
```python
ctx.get(
    ids=["skill-md-whole"],
    mode="skeleton",  # Solo ## headings + code blocks
    budget_token_est=200
)
```

---
