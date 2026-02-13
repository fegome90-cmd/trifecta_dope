#!/usr/bin/env bash
# Demo: Sidecar ↔ Trifecta Integration
# Shows complete automatic workflow

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REPO_ROOT="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope"
SIDECAR_DIR="/tmp/sidecar"

echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Sidecar ↔ Trifecta Integration Demo${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Show current index
echo -e "${YELLOW}[1/4] Current WO Index${NC}"
echo "────────────────────────────────────────────────────────────"
if [ -f "${REPO_ROOT}/_ctx/index/wo_worktrees.json" ]; then
    echo -e " ${GREEN}✓${NC} Index exists"
    jq -r '.work_orders | length' "${REPO_ROOT}/_ctx/index/wo_worktrees.json"
    echo "  work orders indexed"
else
    echo -e " ${RED}✗${NC} Index not found - generating..."
    cd "${REPO_ROOT}"
    uv run python scripts/export_wo_index.py
fi
echo ""

# Step 2: Show index structure
echo -e "${YELLOW}[2/4] Index Structure${NC}"
echo "────────────────────────────────────────────────────────────"
echo "Location: ${REPO_ROOT}/_ctx/index/wo_worktrees.json"
echo ""
echo "Sample entry:"
jq '.work_orders[0:2] | del(.last_error, .closed_at, .created_at)' \
    "${REPO_ROOT}/_ctx/index/wo_worktrees.json" 2>/dev/null || echo "  (no entries)"
echo ""

# Step 3: Show Sidecar plugin location
echo -e "${YELLOW}[3/4] Sidecar Plugin${NC}"
echo "────────────────────────────────────────────────────────────"
if [ -f "${SIDECAR_DIR}/bin/sidecar" ]; then
    echo -e " ${GREEN}✓${NC} Sidecar built: ${SIDECAR_DIR}/bin/sidecar"
else
    echo -e " ${RED}✗${NC} Sidecar not built - run: cd ${SIDECAR_DIR} && make build"
    exit 1
fi
echo ""

# Step 4: Show how plugin reads index
echo -e "${YELLOW}[4/4] Automatic Flow${NC}"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "When WO status changes:"
echo "  1. trifecta take WO-XXXX"
echo "  2. Hook executes: scripts/export_wo_index.py"
echo "  3. JSON regenerated: _ctx/index/wo_worktrees.json"
echo ""
echo "When Sidecar starts:"
echo "  1. Plugin Init() called with WorkDir"
echo "  2. Reads: <WorkDir>/_ctx/index/wo_worktrees.json"
echo "  3. Validates schema: trifecta.sidecar.wo_index.v1"
echo "  4. Displays WOs with filters"
echo ""

# Step 5: Run Sidecar
echo -e "${YELLOW}[5/4] Launch Sidecar${NC}"
echo "────────────────────────────────────────────────────────────"
echo ""
echo -e "${GREEN}Command:${NC}"
echo "  ${SIDECAR_DIR}/bin/sidecar -project ${REPO_ROOT}"
echo ""
echo -e "${BLUE}Keybindings:${NC}"
echo "  R - Refresh index"
echo "  r - Filter running"
echo "  p - Filter pending"
echo "  d - Filter done"
echo "  a - Show all"
echo "  Enter - View details"
echo "  q - Quit"
echo ""
read -p "Press Enter to launch Sidecar (or Ctrl+C to cancel)... "

"${SIDECAR_DIR}/bin/sidecar" -project "${REPO_ROOT}"
