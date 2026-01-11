### 5.1 Riesgo R1: Secrets en Bundles

**Descripción**: Bundle puede capturar `.env`, API keys en file_reads, o secrets en tool_call results.

**Impacto**: CRÍTICO (filtración de credenciales).

**Probabilidad**: ALTA (sin redaction, inevitable en 1–2 runs).

**Mitigación**:
1. **Preventivo**: Denylist estricta en `ctx_bundle_rules.yaml` (`.env`, `*secret*`, `*password*`).
2. **Detective**: Pre-scan con regex patterns antes de bundle pack (ver 4.3 redaction).
3. **Correctivo**: Si secrets detectados → fail bundle pack con error ruidoso (no silent).
4. **Validación**: Test `test_bundle_pack_blocks_secrets` con `.env` mock.

**Métrica**: `secrets_detected_count` > 0 → FAIL build.

---
