#!/usr/bin/env bash
# Tripwire: Audit-Grade Report Verification
# Purpose: Anti-regression check for AST cache persist-cache merge readiness
# Location: scripts/verify_audit_grade_report.sh
#
# Usage: bash scripts/verify_audit_grade_report.sh
#        DOC=path/to/doc.md bash scripts/verify_audit_grade_report.sh

set -e

DOC="${DOC:-docs/reports/merge_readiness_ast_cache_audit_grade.md}"
ARTIFACTS="docs/reports/artifacts/ast_cache_persist"

echo "=== AST Cache Persist-Cache: Audit-Grade Verification ==="
echo "Document: $DOC"
echo ""
echo "=== Phase 1: Static Validation ==="

# Check 1: No fish syntax
if rg -n "set DB \(" "$DOC" >/dev/null 2>&1; then
    echo "❌ NO-PASS: fish syntax present"
    exit 1
fi
echo "✅ No fish syntax"

# Check 2: Bash syntax present
if ! rg -n "DB=\\\$\(" "$DOC" >/dev/null 2>&1; then
    echo "❌ NO-PASS: missing bash DB=\$(...)"
    exit 1
fi
echo "✅ Bash DB=\$(...) syntax present"

# Check 3: Tee commands present
if ! rg -n '2>&1.*tee' "$DOC" >/dev/null 2>&1; then
    echo "❌ NO-PASS: E2/E4 missing tee"
    exit 1
fi
echo "✅ Tee commands present"

# Check 4: No globs in anchors (allow in commands)
# The glob ast_cache_*.db should only appear in bash find commands
if rg -q  'ast_cache_\*' "$DOC" && ! rg -q 'find.*ast_cache_\*' "$DOC"; then
    echo "❌ NO-PASS: glob in non-command context"
    exit 1
fi
echo "✅ No globs in anchors"

# Check 5: Privacy policy applied
if ! rg -n "<REDACTED>" "$DOC" >/dev/null 2>&1; then
    echo "❌ NO-PASS: <REDACTED> policy not applied"
    exit 1
fi
echo "✅ Privacy policy applied"

echo ""
echo "=== Phase 2: Artifacts Integrity ==="

# Check artifact files exist
REQUIRED_FILES=(
    "gate_all_extract.log"
    "run1_extract.log"
    "run2_extract.log"
    "cache_rowcount.log"
    "pytest_unit.log"
    "checksums.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$ARTIFACTS/$file" ]; then
        echo "❌ NO-PASS: Missing artifact: $file"
        exit 1
    fi
done
echo "✅ All 6 artifact files present"

# Verify checksums
if ! (cd "$ARTIFACTS" && shasum -c checksums.txt >/dev/null 2>&1); then
    echo "❌ NO-PASS: Checksum verification failed"
    exit 1
fi
echo "✅ Checksums verified"

echo ""
echo "=== Phase 3: Semantic Checks (from artifacts) ==="

# Check pytest
if ! rg -q "2 passed" "$ARTIFACTS/pytest_unit.log"; then
    echo "❌ NO-PASS: pytest unit tests did not pass"
    exit 1
fi
echo "✅ Unit tests: 2 passed"

# Check cache rowcount
if ! rg -q "^1$" "$ARTIFACTS/cache_rowcount.log"; then
    echo "❌ NO-PASS: Cache rowcount not 1"
    exit 1
fi
echo "✅ Cache: 1 row written"

# Check gate
if ! rg -q "GATE PASSED" "$ARTIFACTS/gate_all_extract.log"; then
    echo "❌ NO-PASS: Gate did not pass"
    exit 1
fi
echo "✅ Gate: PASSED"

echo ""
echo "=============================="
echo "✅ ALL CHECKS PASS"
echo "=============================="
echo ""
echo "Evidence preserved in: $ARTIFACTS"
exit 0
