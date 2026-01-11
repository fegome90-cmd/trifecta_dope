## 📊 Perfiles de Output

| Perfil | Propósito | Contract |
|--------|-----------|----------|
| `diagnose_micro` | Máximo texto, código ≤3 líneas | `code_max_lines: 3` |
| `impl_patch` | Patch con verificación | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations]` |
| `plan` | DoD + pasos (sin código) | `forbid: [code_blocks]` |
| `handoff_log` | Bitácora + handoff | `append_only: true` |
