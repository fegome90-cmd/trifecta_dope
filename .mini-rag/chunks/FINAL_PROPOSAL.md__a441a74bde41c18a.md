### Opción B: Metadata Flag (como frontmatter YAML)
```json
{
  "cmd": "session.entry",
  "x": {
    "category": "narrative",  // vs "observability"
    "tags": [...]
  }
}
```

**Ventaja**: Separación explícita, queryable
```bash
jq 'select(.x.category == "narrative")' events.jsonl
```

**Recomendación**: Usar **Opción A** (cmd prefijo) + **Opción B** (metadata) combinadas
- Prefijo para filter rápido (grep)
- Metadata para queries semánticos

---
