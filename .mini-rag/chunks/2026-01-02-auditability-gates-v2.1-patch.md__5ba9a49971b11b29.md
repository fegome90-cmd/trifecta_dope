## C) Blocker 1: G2 Path Hygiene — sanitized_dump() CORREGIDO

**Problema identificado:** v2.0 solo sanitizaba `repo_root` y `file://`, pero NO paths absolutos arbitrarios en otros campos (ej: `source_files[].path`).

**Patch completo (reemplazar versión v2.0):**
