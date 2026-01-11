#### Comando 1: `trifecta session append`

**Evidencia de uso actual**:
```bash
$ uv run trifecta session append --help
Usage: trifecta session append [OPTIONS]

Options:
  * --segment   -s  TEXT  Target segment path (required)
  * --summary       TEXT  Summary of work done (required)
    --files         TEXT  Comma-separated list of files touched
    --commands      TEXT  Comma-separated list of commands run
```

**Tests existentes**:
```
tests/unit/test_session_and_normalization.py:
- test_session_append_creates_file
- test_session_append_appends_second_entry
- test_session_append_includes_pack_sha_when_present
```

**Output contract actual**:
```
✅ Created _ctx/session_trifecta_dope.md
   Summary: <summary text>
```
O:
```
✅ Appended to _ctx/session_trifecta_dope.md
   Summary: <summary text>
```

**Output contract propuesto (V1)**:
```json
{
  "status": "ok",
  "message": "✅ Appended to telemetry",
  "entry_id": "session:abc1234567"
}
```

**PROBLEMA**: ⚠️ **Rompe backward compatibility** - cambio en output format

**FIX REQUERIDO**: Mantener output text actual + añadir entry_id opcional:
```
✅ Appended to _ctx/session_trifecta_dope.md (entry: session:abc1234567)
   Summary: <summary text>
```

**JSON Schema para validación**: ❌ **MISSING** - SCOOP no incluye schema file real

**BLOCKER #1**: Crear `docs/schemas/session_append_output.schema.json` con validator test

---
