### Escritura Atómica + Lock
- **Atomic Write**: `tmp -> fsync -> rename`.
- **Lock**: `_ctx/.lock` mediante `fcntl`.
