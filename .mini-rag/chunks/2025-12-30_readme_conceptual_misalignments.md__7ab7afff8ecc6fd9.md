### 2. **Script legacy `ingest_trifecta.py` (L210-218)**

**Ubicación**: `README.md:210-218`

**Problema**:

```bash
# Generar context_pack.json en _ctx/
python scripts/ingest_trifecta.py --segment debug_terminal
```

**Por qué es un problema**:

- Recomienda script legacy cuando existe `trifecta ctx build` (CLI oficial)
- Contradice "usar IDEAS no PRODUCTOS" (filosofía del proyecto)
- Riesgo de divergencia entre script y CLI

**Corrección propuesta**:

```markdown
### Generar Context Pack

```bash
