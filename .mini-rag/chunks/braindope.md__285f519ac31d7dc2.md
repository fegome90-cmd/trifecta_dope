## Catálogo de Perfiles (4 máximo)
| Profile | Propósito | Output Contract |
|---------|-----------|----------------|
| `diagnose_micro` | Máximo texto explicativo, código ≤3 líneas | `code_max_lines: 3` |
| `impl_patch` | Patch pequeño con verificación | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations, essays]` |
| `plan` | DoD + pasos + gates (sin código) | `forbid: [code_blocks]` |
| `handoff_log` | Bitácora + handoff + next request | `append_only: true, require: [History, NextUserRequest]` |
