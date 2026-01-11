## D) audit_repro.sh (CORREGIDO v2.1 — Bash 3.2 compatible)

**Problemas identificados:**
- `declare -A` no funciona en bash 3.2 (macOS por defecto)
- `jq ... 2>/dev/null` contradice AP6
- G3 mezcla stdout/stderr
