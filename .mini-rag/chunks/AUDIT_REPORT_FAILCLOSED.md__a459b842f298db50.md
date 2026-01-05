### A.2) Features "NUNCA" (confirmadas NO EXISTEN)

**Evidence-based verification**:

1. **session_journal.jsonl (JSONL separado)**
   ```bash
   $ ls _ctx/session*.jsonl 2>&1
   ls: _ctx/session*.jsonl: No such file or directory
   ```
   **Confirmado**: ✅ NO EXISTE - no hay nada que borrar

2. **Auto-detección de tool use**
   ```bash
   $ rg "auto.*detect.*tool|parse.*tool.*use" src/ --type py
   (no matches)
   ```
   **Confirmado**: ✅ NO EXISTE - no hay parser de tool use

3. **Background daemon / script**
   ```bash
   $ rg "daemon.*session|background.*script" . --type py --type sh
   (no matches)
   ```
   **Confirmado**: ✅ NO EXISTE - no hay daemon

4. **session query command**
   ```bash
   $ rg "session.*query|query.*session" src/ --type py
   (no matches)
   ```
   **Confirmado**: ✅ NO EXISTE - comando nuevo (no borrado)

5. **session load command**
   ```bash
   $ uv run trifecta session load --help 2>&1
   Error: No such command 'load'
   ```
   **Confirmado**: ✅ NO EXISTE - comando nuevo (no borrado)

**verdict**: ✅ **ELIMINATION GATE NO APLICA** - nada se está borrando, todas son features nuevas o inexistentes

---
