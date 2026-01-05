#### Step 2: Create Infrastructure (Blockers #2, #5, #7)

**2a) JSON Schemas**:
```bash
mkdir -p docs/schemas
```

`docs/schemas/session_query_clean.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["ts", "summary", "type", "outcome"],
    "properties": {
      "ts": {"type": "string", "format": "date-time"},
      "summary": {"type": "string", "minLength": 1},
      "type": {"enum": ["debug", "develop", "document", "refactor"]},
      "files": {"type": "array", "items": {"type": "string"}},
      "commands": {"type": "array", "items": {"type": "string"}},
      "outcome": {"enum": ["success", "partial", "failed"]},
      "tags": {"type": "array", "items": {"type": "string"}}
    },
    "additionalProperties": false
  }
}
```

**2b) Benchmark script**: (ver código en C.3)

**2c) Privacy test**: (ver código en D.3)

**Test Gate**:
```bash
pytest tests/acceptance/test_no_privacy_leaks.py -v
# MUST pass (after implementing session query)
```

---
