### A.3) RIESGO DETECTADO: ¿Qué pasa con session.md existente?

**Evidencia actual**:
```bash
$ wc -l _ctx/session_trifecta_dope.md
397 _ctx/session_trifecta_dope.md
```

**Estado**: session.md tiene 397 líneas de contenido histórico

**SCOOP dice**: "session.md se mantiene como log humano, puede generarse desde JSONL (V2)"

**PREGUNTA CRÍTICA**: ¿El cambio V1 hace que session.md **deje de actualizarse**?

**Respuesta del código actual** (session_append:L1280-L1341):
```python
# Actualmente escribe SOLO a session.md
session_file.write_text(...) # o f.write(...)
typer.echo(f"✅ Appended to {session_file.relative_to(segment_path)}")
```

**PROPUESTA V1**: Escribir a AMBOS (telemetry.jsonl + session.md)

**verdict**: ⚠️ **NO HAY BORRADO**, pero SCOOP debe aclarar:
- V1: ¿session append escribe a AMBOS o solo telemetry?
- Si solo telemetry → session.md queda congelado (PÉRDIDA de log humano)
- Si ambos → sincronización manual (complejidad añadida)

**RECOMENDACIÓN**: V1 debe escribir a AMBOS para mantener backward compat total.

---
