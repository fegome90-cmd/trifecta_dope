#!/usr/bin/env bash
set -u # Don't use -e yet, we'll handle failures manually

# Test script for prevent_manual_wo_closure.sh hook
# This script simulates various commit scenarios and asserts the hook's exit code.

REPO_ROOT=$(git rev-parse --show-toplevel)
SCRIPTS_DIR="$REPO_ROOT/scripts/hooks"
HOOK_SCRIPT="$SCRIPTS_DIR/prevent_manual_wo_closure.sh"
TEST_WO_ID="WO-99$(date +%S)" # WO-99 + seconds for semi-uniqueness
TEST_WO_FILE="_ctx/jobs/done/$TEST_WO_ID.yaml"
COMMIT_MSG_FILE="/tmp/test_commit_msg"

log_test() { echo ">>> TEST: $*"; }
fail_test() { echo "FAIL: $*" >&2; cleanup_test; exit 1; }

setup_test_wo() {
  mkdir -p "_ctx/jobs/done"
  cat > "$TEST_WO_FILE" <<EOF
id: $TEST_WO_ID
status: done
title: Test WO
verified_at_sha: initial-sha
EOF
  git add "$TEST_WO_FILE"
  # Commit with bypass to set up the baseline
  # We use --no-verify to ensure this setup commit always works
  TRIFECTA_HOOKS_DISABLE=1 TRIFECTA_WO_BYPASS_REASON="test setup" git commit -m "chore(wo): initial test setup for $TEST_WO_ID" --no-verify >/dev/null 2>&1
}

cleanup_test() {
  log_test "Cleanup..."
  rm -f "$COMMIT_MSG_FILE"
  if [[ -f "$TEST_WO_FILE" ]]; then
    git reset HEAD "$TEST_WO_FILE" >/dev/null 2>&1
    rm -f "$TEST_WO_FILE"
  fi
}

trap cleanup_test EXIT

# --- Scenario 1: Metadata-only update with proper message (PASS) ---
log_test "Metadata-only update with proper message (SHOULD PASS)"
setup_test_wo
# Simulate update to verified_at_sha
sed -i '' 's/initial-sha/new-sha/' "$TEST_WO_FILE"
git add "$TEST_WO_FILE"
echo "chore(wo): verify $TEST_WO_ID" > "$COMMIT_MSG_FILE"

# Run hook
if ! bash "$HOOK_SCRIPT" "$COMMIT_MSG_FILE"; then
  fail_test "Legitimate metadata update failed"
fi
echo "Result: PASS"

# --- Scenario 2: Manual move / new file in done/ (FAIL) ---
log_test "Manual move / new file in done/ (SHOULD FAIL)"
# Use a DIFFERENT ID to simulate a manual move
NEW_ID="WO-MANUAL-$(date +%s)"
NEW_FILE="_ctx/jobs/done/$NEW_ID.yaml"
cat > "$NEW_FILE" <<EOF
id: $NEW_ID
status: done
EOF
git add "$NEW_FILE"
echo "chore(wo): close $NEW_ID" > "$COMMIT_MSG_FILE"

if bash "$HOOK_SCRIPT" "$COMMIT_MSG_FILE" >/dev/null 2>&1; then
  rm -f "$NEW_FILE"
  git reset HEAD "$NEW_FILE" >/dev/null 2>&1
  fail_test "Manual new file in done/ unexpectedly passed"
fi
rm -f "$NEW_FILE"
git reset HEAD "$NEW_FILE" >/dev/null 2>&1
echo "Result: FAIL (correctly blocked)"

# --- Scenario 3: Non-metadata update (FAIL) ---
log_test "Non-metadata update (SHOULD FAIL)"
# Setup test WO again (previous one was committed)
# Change title
sed -i '' 's/Test WO/Modified Title/' "$TEST_WO_FILE"
git add "$TEST_WO_FILE"
echo "chore(wo): verify $TEST_WO_ID" > "$COMMIT_MSG_FILE"

if bash "$HOOK_SCRIPT" "$COMMIT_MSG_FILE" >/dev/null 2>&1; then
  fail_test "Structural edit to done/ WO unexpectedly passed"
fi
git reset HEAD "$TEST_WO_FILE" >/dev/null 2>&1
git checkout "$TEST_WO_FILE" >/dev/null 2>&1
echo "Result: FAIL (correctly blocked)"

# --- Scenario 4: Metadata update with wrong commit message (FAIL) ---
log_test "Metadata update with wrong commit message (SHOULD FAIL)"
sed -i '' 's/initial-sha/new-sha-2/' "$TEST_WO_FILE"
git add "$TEST_WO_FILE"
echo "fix: update metadata" > "$COMMIT_MSG_FILE"

if bash "$HOOK_SCRIPT" "$COMMIT_MSG_FILE" >/dev/null 2>&1; then
  fail_test "Metadata update with bad message unexpectedly passed"
fi
git reset HEAD "$TEST_WO_FILE" >/dev/null 2>&1
git checkout "$TEST_WO_FILE" >/dev/null 2>&1
echo "Result: FAIL (correctly blocked)"

log_test "ALL HOOK TESTS PASSED"
