## B) PATCH: Gates G3 (tabla) — STATUS/CODE limpios

**Problema v2.1:** Variables STATUS/CODE se capturan desde pipe que puede mezclar stderr con stdout.

**v2.1 → v2.2 diff (reemplazar fila G3 en tabla A):**

| Gate | Criterio PASS | Comando Exacto (stdout/stderr separados) | Evidencia Requerida | APs Evitados |
|------|---------------|----------------------------------------|---------------------|-------------|
| **G3: ast symbols** | JSON parseable + NO FILE_NOT_FOUND | `uv run trifecta ast symbols sym://python/mod/context_service > /tmp/g3_ast.json 2> /tmp/g3_ast.stderr; AST_RC=$?; cat /tmp/g3_ast.json \| jq -r '.status' > /tmp/g3_status.txt 2> /tmp/g3_jq_stderr.txt; STATUS=$(cat /tmp/g3_status.txt); CODE=$(cat /tmp/g3_ast.json \| jq -r '.errors[0].code // "null"' > /tmp/g3_code.txt 2> /tmp/g3_jq_stderr.txt; cat /tmp/g3_code.txt); echo "G3_AST=$AST_RC"; echo "G3_STATUS=$STATUS"; echo "G3_CODE=$CODE"` | (1) `/tmp/g3_ast.json` (JSON stdout), (2) `/tmp/g3_ast.stderr` (cmd stderr), (3) `/tmp/g3_status.txt`, `/tmp/g3_code.txt` (jq output limpio), (4) `/tmp/g3_jq_stderr.txt` (jq stderr) | AP1 (jq stdout → archivo → variable), AP6 (todo capturado), AP7 (variables limpias) |

**NOTAS SOBRE RCs (v2.2):**
