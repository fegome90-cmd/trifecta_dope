## 🔴 PROBLEMA #3: Privacidad y Redacción

**Telemetry policy** (líneas 159-166):
> "Paths: Always use `_relpath` to log relative paths. NEVER log absolute paths."  
> "Segment: Log `segment_id` (SHA-256 hash prefix), not `segment_path`."

**Session necesita**:
- Paths legibles de archivos touched (ej: `src/infrastructure/lsp_client.py`)
- Summary texto libre del agente (puede contener info sensible)

**CONTRADICCIÓN**:
- Telemetry está hardened para NO leakear PII
- Session NECESITA info legible (paths, summaries)

**Si extiendes telemetry**: ¿Relajas las reglas de redacción? Eso degrada la seguridad.

---
