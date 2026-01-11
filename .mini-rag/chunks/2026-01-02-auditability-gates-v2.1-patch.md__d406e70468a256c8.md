## Resumen de Cambios v2.0 → v2.1

| Issue | v2.0 | v2.1 |
|-------|------|------|
| G2 RC | `$?` (incorrecto) | `${PIPESTATUS[0]}` (correcto) |
| G3 JSON | `2>&1 \| tee` luego parse | `>file.json 2>file.stderr` (separado) |
| G3 parse_error | Ignorado (PASS falso) | Tratado como FAIL |
| sanitized_dump() | Solo repo_root + file:// | TODOS los paths absolutos |
| Bash arrays | `declare -A` | Variables simples |
| jq stderr | `2>/dev/null` | Capturado en log |

---
