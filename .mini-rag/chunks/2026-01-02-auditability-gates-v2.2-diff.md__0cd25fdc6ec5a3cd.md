## Resumen: Por qué v2.2 elimina PASS falsos

| Issue | v2.1 | v2.2 | PASS falso eliminado |
|-------|------|------|---------------------|
| **JSON serializable** | `model_dump()` puede retornar Path | `model_dump(mode="json")` | Previene `TypeError` que hacía fallar sanitized_dump() |
| **STATUS contamination** | `STATUS=$(jq ... 2>&1 | tee ...)` | `STATUS=$(cat archivo.txt)` con stderr separado | STATUS/CODE están limpios, parse_error detectable |
| **jq stderr** | `2>/dev/null` o mezclado | Capturado en archivo dedicado | jq errors visibles, no ocultos |
| **Test filenames** | Nombres inventados | Nombres descubiertos via rg | Test no falla por nombre incorrecto |

---
