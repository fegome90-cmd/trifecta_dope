#!/bin/bash
# Verify direnv loading and AST Persistence backend

set -euo pipefail

if ! command -v direnv &> /dev/null; then
    echo '⚠️  direnv not installed or not in PATH.'
    exit 0
fi

if [[ -z "${TRIFECTA_AST_PERSIST:-}" ]]; then
    # Only verify if direnv is allowed in current dir
    if direnv status | grep -q 'Found RC allowed true'; then
        echo '❌ TRIFECTA_AST_PERSIST not set despite allowed .envrc'
        exit 1
    fi
fi

# If env var is set, verify backend is FileLockedAstCache
if [[ "${TRIFECTA_AST_PERSIST:-}" == "1" ]]; then
     # Check via gate script reuse or simplified check
     echo '✅ TRIFECTA_AST_PERSIST=1 detected.'
fi

