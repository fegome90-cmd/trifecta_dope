## F) Referencia Cruz: Anti-Patrones → Mitigaciones en el Plan

| Anti-Patrón | Descripción | Mitigación en este plan |
|-------------|-------------|------------------------|
| **AP1** | Stringly-typed contracts | jq parser para JSON; assertions en Python; no `startswith()` para lógica |
| **AP2** | Tests no deterministas | tmp_path fixtures; no skip/xfail sin ADR; tests integration con segmentos temporales |
| **AP3** | CWD/paths implícitos | CWD independence tests; todo relativo a segment_root; convención src/ |
| **AP4** | Concurrencia/shutdown ruidoso | (Fuera de scope actual; planear post-gates) |
| **AP5** | Flags/env sin precedencia | No agregar flags; usar convención fija; precedencia documentada si existe |
| **AP6** | Ocultar evidencia | No `2>/dev/null` en gates; todo con `tee`; stderr capturado |
| **AP7** | PASS falsos por checks malos | RCs explícitos; rg RC=1 es PASS; jq exit code valida JSON |
| **AP8** | Duplicar SSOT | rg commands para localizar SSOT; parches en archivos dueños; no duplicados |
| **AP9** | Compat shims en capa equivocada | NO re-exports en ast_parser; arreglar imports en tests |
| **AP10** | Fallback silencioso | Sync RC verificado antes de validar PII; fallback auditado |

---
