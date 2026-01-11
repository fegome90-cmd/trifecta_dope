```bash
#!/usr/bin/env bash
# audit_repro.sh — Evidence capture para trifecta_dope auditability gates
# POLÍTICA: No abortar en fallos, capturar todo, calcular gates al final con RC explícitos
# Usage: cd /path/to/trifecta_dope && bash audit_repro.sh

set +e  # CRÍTICO: No abortar en fallos

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARTIFACTS="/tmp/trifecta_audit_${TIMESTAMP}"
mkdir -p "${ARTIFACTS}"

# Variables para gate results (RCs)
declare -A GATE_RC
GATE_RC[G1]=1
GATE_RC[G2]=1
GATE_RC[G3]=1
GATE_RC[G4]=255  # 255 = SKIP

echo "=== Trifecta Auditability Evidence Capture ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Artifacts: ${ARTIFACTS}"
echo ""

# ============================================================================
# G0: Baseline (git state)
# ============================================================================
echo "=== G0: Git Baseline ==="
git rev-parse HEAD > "${ARTIFACTS}/git_sha.txt" 2>&1
git status --porcelain > "${ARTIFACTS}/git_status.txt" 2>&1
echo "Git SHA: $(cat ${ARTIFACTS}/git_sha.txt)"
echo "Git dirty: $(test -s ${ARTIFACTS}/git_status.txt && echo 'yes' || echo 'no')"
echo ""

# ============================================================================
# G1: pytest collecting (FAIL-CLOSED: ERROR collecting = FAIL)
# ============================================================================
echo "=== G1: Pytest Collection ==="
echo "Running: uv run
