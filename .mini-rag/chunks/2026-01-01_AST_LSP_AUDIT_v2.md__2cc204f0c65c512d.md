### 3. ❌ "No rollback if LSP diverges"
**Why bad here:** Agent edits → LSP caches stale AST → wrong diagnostics.  
**Lean alternative:** Version per edit, explicit commit/rollback, no persistence in v0.
