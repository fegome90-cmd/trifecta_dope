## CLI Oficial (Actualizado)

**Comandos recomendados**:
```bash
# Build context pack
trifecta ctx build --segment .

# Validate integrity
trifecta ctx validate --segment .

# Search context
trifecta ctx search --segment . --query "keyword" --limit 5

# Get specific chunks
trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900
```

**Script legacy** (solo para referencia histórica):
- `scripts/ingest_trifecta.py` → Ver secciones siguientes para contexto

---
