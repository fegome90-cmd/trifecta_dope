#### Comando 2: `trifecta session query` (NUEVO)

**Estado actual**: ❌ NO EXISTE

**Evidencia**:
```bash
$ rg "def.*session.*query" src/
(no matches)
```

**Contract propuesto**: Ver SCOOP sección 4, item 2

**JSON Schema propuesto**:
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["ts", "summary", "type", "outcome"],
    "properties": {
      "ts": {"type": "string", "format": "date-time"},
      "summary": {"type": "string"},
      "type": {"enum": ["debug", "develop", "document", "refactor"]},
      ...
    }
  }
}
```

**PROBLEMA**: ❌ Schema está en SCOOP markdown, NO en archivo `.schema.json` separado

**BLOCKER #2**: Crear schema files + validator tests ANTES de implementar

---
