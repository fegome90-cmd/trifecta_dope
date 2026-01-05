```bash
#!/usr/bin/env bash
# audit_repro.sh v2.1 — Evidence capture para trifecta_dope auditability gates
#
# CAMBIOS desde v2.0:
# - Sin arrays asociativos (bash 3.2 compatible)
# - G3: stdout/stderr separados
# - jq stderr capturado (no 2>/dev/null)
# - parse_error tratado como FAIL
#
# POLÍTICA (AP6, AP7):
# - NO abortar en fallos (capturar todo)
# - TODO va a archivos via tee (no /dev/null en gates)
# - RCs preservados con ${PIPESTATUS[n]}
# - Gates calculados al final con RCs explícitos

set +e  # CRÍTICO: No abortar en fallos (AP6)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARTIFACTS="/tmp/trifecta_audit_${TIMESTAMP}"
mkdir -p "${ARTIFACTS}"

# Variables simples (bash 3.2 compatible - NO declare -A)
G1_RC=1
G2_SYNC_RC=1
G2_RG_RC=1
G2_OVERALL=1
G3_AST_RC=1
G3_STATUS=""
G3_CODE=""
G3_OVERALL=1
G4_OVERALL=255  # 255 = SKIP

echo "=== Trifecta Auditability Evidence Capture v2.1 ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Artifacts: ${ARTIFACTS}"
echo ""

# Verificar bash version (opcional, para debugging)
echo "Bash version: $BASH_VERSION"
echo ""

# ============================================================================
# G0: Baseline (git state)
# ============================================================================
echo "=== G0: Git Baseline ==="
git rev-parse HEAD > "${ARTIFACTS}/git_sha.txt" 2>&1
git status --porcelain > "${ARTIFACTS}/git_status.txt" 2>&1
echo "Git SHA
