### D.1) Threat Model del SCOOP (sección 8)

**Vectores identificados**:
1. Error messages con stack traces
2. Query output con `--format raw`
3. Telemetry JSONL direct read

**Datos prohibidos**:
- Paths absolutos: `/Users/`, `/home/`, `C:\Users\`
- API keys / tokens
- Segment full paths (debe ser hash)

**PROBLEMA**: ⚠️ Código actual de `session_append` **USA paths absolutos**:

**Evidencia** (cli.py:L1293):
```python
segment_path = Path(segment).resolve()  # ← .resolve() = absolute path
session_file = segment_path / "_ctx" / f"session_{segment_name}.md"
```

**Luego** (cli.py:L1336):
```python
typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
                                      # ↑ relativiza, OK
```

**PERO**: Si `session_file.relative_to()` falla (segment_path no es parent), se usa absolute path

**RISK**: ⚠️ **Privacy leak** en error messages

---
