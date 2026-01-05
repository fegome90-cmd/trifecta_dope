## 8) Safety + Privacy (threat model)

**DATOS PROHIBIDOS**:

1. **Paths absolutos** — Ejemplo: `/Users/felipe_gonzalez/Developer/...`
2. **API keys / tokens** — Ejemplo: `GEMINI_API_KEY=xxx`
3. **Segment full paths** — Debe ser hash: `segment_id: "6f25e381"` NO `/path/to/segment`

**THREAT MODEL** (dónde puede leakear):

**Vector 1**: Error messages con stack traces
  Escenario: `session append` falla, exception incluye path absoluto
  Test:
  ```bash
  # Trigger error y verificar que output NO tiene paths absolutos
  uv run trifecta session append -s /tmp/nonexistent --summary "test" 2>&1 | \
    rg "/Users/|/home/" && exit 1 || exit 0
  ```

**Vector 2**: Query output con `--format raw`
  Escenario: Usuario usa raw format, expone campos internos
  Test:
  ```bash
  uv run trifecta session query -s . --last 1 --format raw | \
    rg "/Users/|/home/" && exit 1 || exit 0
  ```

**Vector 3**: Telemetry JSONL direct read
  Escenario: Alguien lee telemetry.jsonl y encuentra paths en args/result
  Test:
  ```bash
  rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | \
    rg "/Users/|/home/" && exit 1 || exit 0
  ```

**REDACTION POLICY**:

Paths: Usar `_relpath(repo_root, path)` siempre - solo rutas relativas
Secretos: Never log - redactar con `***` si aparecen en args
Segment: Usar `hashlib.sha256(segment_path).hexdigest()[:8]` - NO path directo

**CI gate**:
