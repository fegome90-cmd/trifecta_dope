## 11) Time Horizon + Tech Debt (con deadline hard)

**TIME HORIZON**:

V1 deadline: **2026-01-15** (2 semanas desde hoy)

V2 tentativo: **2026-02-15** (1 mes post-V1) - features:
- session.md auto-generation
- Telemetry rotation integrada

**TECH DEBT ACEPTADA**:

1. **Grep filter en lugar de índices**
   Plan de pago:
   - Deadline: **ACCEPTED PERMANENT** (grep es suficiente hasta 100K events)
   - Owner: N/A
   - Justificación: Pragmatismo > optimización prematura. Grep < 50ms es acceptable.

2. **Schema limpio manual (jq filter) en lugar de Pydantic projection**
   Plan de pago:
   - Deadline: V2 (2026-02-15) - refactor a Pydantic model con `.model_dump(exclude=...)`
   - Owner: Felipe
   - Si no se paga: Aceptable (jq funciona, solo menos elegante)

3. **Sin validación de JSON Schema en runtime**
   Plan de pago:
   - Deadline: 2026-01-20 (1 semana post-V1 merge)
   - Owner: Felipe
   - Justificación: V1 puede lanzar sin validator, agregar en V1.1 hotfix

**"NUNCA" LIST**:

1. **Auto-detección de tool use** — Razón: Costo prohibitivo (15h) vs valor bajo (conveniencia)
2. **session_journal.jsonl separado** — Razón: Duplicación innecesaria, anti-goal de simplicidad
3. **Background daemon** — Razón: Operational nightmare, violates reliability principle

---
