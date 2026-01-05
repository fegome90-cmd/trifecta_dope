# Correcciones v2.1 — Gates y Script (PATCH para plan v2.0)

> Aplicar estos parches sobre `docs/plans/2026-01-02-auditability-gates-v2-antipatterns.md`
>
> **Problemas corregidos:**
> - G2: RC mal capturado en tabla ($? → PIPESTATUS[0])
> - G3: JSON parsing inseguro (mezcla stdout/stderr, parse_error no tratado)
> - sanitized_dump(): sanitización incompleta para paths arbitrarios
> - audit_repro.sh: declare -A no portátil en bash 3.2
> - jq stderr: 2>/dev/null contradice AP6

---
