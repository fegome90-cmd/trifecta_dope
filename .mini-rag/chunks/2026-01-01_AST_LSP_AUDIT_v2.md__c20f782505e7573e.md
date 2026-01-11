### 6. ❌ "Logging unredacted code in diagnostics"
**Why bad here:** `.env` file incomplete → LSP emits "variable not found" → secret logged.  
**Lean alternative:** Hard denylist (.env, secrets), redact before telemetry, scan pre-parse.
