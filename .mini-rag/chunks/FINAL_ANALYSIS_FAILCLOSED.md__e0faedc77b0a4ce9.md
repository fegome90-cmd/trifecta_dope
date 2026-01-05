### Opción B: JSONL Source of Truth + Generator (NO RECOMENDADO para V1)

**Decisión**: V1 solo escribe a telemetry, session.md generado desde JSONL

**Problemas**:
1. ❌ Rompe 3 tests existentes
2. ❌ Requiere script generator (2h extra)
3. ❌ session.md deja de ser editable manual
4. ❌ Pérdida de historia si generator falla

**Recomendación**: POSTPONER a V2 (después de validar que dual write funciona)

**Evidencia de decisión** (braindope:L462-L476):
> DECISIONES CONVERGIDAS:  
> 3. session.md se mantiene → Sincronizado con JSONL (puede generarse)

**PERO** sincronización en V1 = dual write, NO generator (generador es V2)

---
