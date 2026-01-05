## Tabla de precedencia detectada (TRIFECTA_*)

| Setting | Default | Env Var | CLI Flag | Conflictos detectados |
|---------|---------|---------|----------|----------------------|
| Telemetry Level | `"lite"` | `TRIFECTA_TELEMETRY_LEVEL` | `--telemetry` | ❌ Env wins over default, flag wins over env. **No conflict.** |
| PD Max Chunks | `None` (unlimited) | `TRIFECTA_PD_MAX_CHUNKS` | `--max-chunks` | ⚠️ Flag overrides env. Test exists in `test_pd_env_var.py`. |
| PD Stop on Evidence | `False` | `TRIFECTA_PD_STOP_ON_EVIDENCE` | `--stop-on-evidence` | ⚠️ Env only checked if flag not provided. |
| Deprecated Policy | `"off"` | `TRIFECTA_DEPRECATED` | N/A | ✅ Env-only, no flag. Tests in `test_deprecations_policy.py`. |

**Conflictos**:
- `TRIFECTA_PD_STOP_ON_EVIDENCE` parsing uses `str.lower() == "true"` — could fail for `"1"` or `"yes"`.
- `TRIFECTA_PD_MAX_CHUNKS` does `int()` with no error handling for non-numeric values.

---
