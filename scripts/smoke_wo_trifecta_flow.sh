#!/usr/bin/env bash
# Smoke test for Trifecta WO flow (happy path)
# Runs in a temp dir to isolate from git worktree resolution logic.
# Usage: ./smoke_wo_trifecta_flow.sh [WO-ID]

set -euo pipefail

WO_ID="${1:-WO-SMOKE}"
ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT

echo "--- Smoke Test: $WO_ID ---"
echo "Running in isolated root: $ROOT"

# Setup isolated environment
mkdir -p "$ROOT/scripts" "$ROOT/src/domain" "$ROOT/src/cli"
cp scripts/ctx_wo_finish.py "$ROOT/scripts/"
cp src/domain/result.py "$ROOT/src/domain/"
cp src/cli/error_cards.py "$ROOT/src/cli/"
touch "$ROOT/src/__init__.py" "$ROOT/src/domain/__init__.py" "$ROOT/src/cli/__init__.py"

# Mock verification scripts (they should pass for happy path)
echo '#!/bin/bash
exit 0' > "$ROOT/scripts/ctx_verify_run.sh"
echo '#!/bin/bash
exit 0' > "$ROOT/scripts/verify.sh"
chmod +x "$ROOT/scripts/ctx_verify_run.sh" "$ROOT/scripts/verify.sh"

# 1. Mock session evidence
echo "Mocking session evidence..."
mkdir -p "$ROOT/_ctx"
echo "[$WO_ID] intent: smoke test start" >> "$ROOT/_ctx/session_trifecta_dope.md"
echo "[$WO_ID] result: smoke test end" >> "$ROOT/_ctx/session_trifecta_dope.md"

# 2. Mock logs verdict
echo "Mocking scope verdict..."
mkdir -p "$ROOT/_ctx/logs/$WO_ID"
echo '{"wo_id": "'"$WO_ID"'", "status": "PASS"}' > "$ROOT/_ctx/logs/$WO_ID/verdict.json"

# 3. Create dummy running WO
echo "Mocking running WO..."
mkdir -p "$ROOT/_ctx/jobs/running" "$ROOT/_ctx/dod"
echo "version: 1
id: $WO_ID
epic_id: E-SMOKE
title: Smoke Test
priority: P3
status: running
dod_id: DOD-DEFAULT
execution:
  engine: trifecta
  required_flow:
    - session.append:intent
    - ctx.sync
    - session.append:result
  segment: .
" > "$ROOT/_ctx/jobs/running/$WO_ID.yaml"

# Create dummy DOD
echo "dod:
  - id: DOD-DEFAULT
    items: []" > "$ROOT/_ctx/dod/dod-default.yaml"

# 4. Generate artifacts
echo "Generating artifacts..."
export PYTHONPATH="$ROOT"

# Init git repo for transaction validation
pushd "$ROOT" > /dev/null
git init
git config user.email "smoke@test.local"
git config user.name "Smoke Test"
git add .
git commit -m "Initial commit"
popd > /dev/null

python3 "$ROOT/scripts/ctx_wo_finish.py" "$WO_ID" --generate-only --root "$ROOT"

# 5. Finish WO
echo "Finishing WO..."
# Commit artifacts to satisfy git status check (except handoff dir which is ignored by script)
# Wait, the script ignores _ctx/handoff/{wo_id}.
# But generate_artifacts creates the directory.
# So we DON'T need to commit artifacts if the script ignores them correctly.
# But verify.sh might complain if we were running it real.
# Here we mock verify.sh.

python3 "$ROOT/scripts/ctx_wo_finish.py" "$WO_ID" --result done --root "$ROOT"

# 6. Verify result
if [[ -f "$ROOT/_ctx/jobs/done/$WO_ID.yaml" ]]; then
    echo "SUCCESS: WO moved to done/"
else
    echo "FAILURE: WO not in done/"
    exit 1
fi
