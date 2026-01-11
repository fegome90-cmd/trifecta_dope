### 5.5 Riesgo R5: Environment Drift (Bundle Replay Fails)

**Descripción**: Bundle capturado en Python 3.12, replay en 3.11 → imports fail, AST incompatible.

**Impacto**: MEDIO (replay no reproducible, bundle inútil para debug).

**Probabilidad**: ALTA (entornos heterogéneos comunes).

**Mitigación**:
1. **Preventivo**: Bundle manifest incluye `python_version`, `uv_version`, `os` (ver 4.1).
2. **Detective**: `trifecta bundle replay` verifica versiones, warn if mismatch.
3. **Correctivo**: Replay mode con `--ignore-env-mismatch` para best-effort (con disclaimer).
4. **Validación**: Test `test_bundle_replay_warns_on_env_mismatch`.

**Métrica**: `replay_env_mismatch_count` (cuántos replays tuvieron drift).

---
