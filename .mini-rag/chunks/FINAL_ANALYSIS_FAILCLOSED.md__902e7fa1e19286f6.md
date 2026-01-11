## 2) QUÉ NO SE BORRA (EXISTENTE) PERO SE TOCA

| Feature | Cambio | Riesgo | Gate/Test | Evidencia |
|:--------|:-------|:-------|:----------|:----------|
| **session append** | Se extiende con dual write (telemetry + session.md) | ⚠️ Si solo escribe a telemetry → rompe 3 tests | `pytest tests/unit/test_session_and_normalization.py -v` MUST PASS | AST symbols: `session_append` L1281 (cli.py) |
| **session.md** | Se mantiene como log humano. Puede generarse desde JSONL (V2) | ⚠️ Si deja de actualizarse → historia congelada | Debe seguir siendo escrito en V1 (dual write) | `_ctx/session_trifecta_dope.md` (21KB, 397 líneas) |
| **telement JSONL** | Se añade event type `session.entry` | ✅ Bajo - event type nuevo, no rompe existentes | Verificar schema sanitization | `_ctx/telemetry/events.jsonl` (606KB, 2186 eventos) |

**Evidencia de riesgo session.md**:
> AUDIT:L79-L95: **PREGUNTA CRÍTICA**: ¿El cambio V1 hace que session.md **deje de actualizarse**?  
> AUDIT:L95: **RECOMENDACIÓN**: V1 debe escribir a AMBOS para mantener backward compat total.

**Tests que NO deben romperse** (AUDIT:L196-L200):
1. `test_session_append_creates_file` - Debe seguir creando session.md
2. `test_session_append_appends_second_entry` - Debe seguir appendeando  
3. `test_session_append_includes_pack_sha_when_present` - Debe incluir pack_sha

**Fix obligatorio** (AUDIT:L204-L212):
