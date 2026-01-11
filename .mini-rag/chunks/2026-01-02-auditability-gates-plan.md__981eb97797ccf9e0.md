=ok o error≠FILE_NOT_FOUND | **DECISIÓN: segment_root/src/ convención fija** |
| **Context Pack Integrity** | `cat _ctx/context_pack.json \| jq -e '.schema_version == 1 and .segment != null'; echo RC=$?` | Integration | RC puede ser 1 si schema corrupto | RC=0 (schema válido) | Validación JSON completo |
