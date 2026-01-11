## G) Ejecución (Handoff)

**Plan v2.0 guardado en** `docs/plans/2026-01-02-auditability-gates-v2-antipatterns.md`.

**Mejoras sobre v1:**
- ✅ AP1: jq parser desde archivo (no pipe string parsing)
- ✅ AP2: Tests con tmp_path fixtures; CWD independence tests
- ✅ AP3: CWD tests tripwire; segment_root como base
- ✅ AP5: Sin flags nuevos; convención fija src/
- ✅ AP6: No `2>/dev/null`; todo con `tee`
- ✅ AP7: RCs explícitos en todos los gates
- ✅ AP8: SSOT localization commands
- ✅ AP9: NO re-exports; imports corregidos
- ✅ AP10: Fallback auditado (sync RC verificado)

**Dos opciones de ejecución:**

**1. Subagent-Driven (esta sesión)** — Despacho subagent fresco por task, review entre pasos, iteración rápida

**2. Parallel Session (separada)** — Nueva sesión con executing-plans, ejecución batch con checkpoints

**¿Cuál prefieres?**
