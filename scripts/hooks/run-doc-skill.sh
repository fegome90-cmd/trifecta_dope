#!/bin/bash
# run-doc-skill.sh — Wrapper for documentation validation
# Usage: bash scripts/hooks/run-doc-skill.sh [OPTIONS]
# Options: --json, --strict, --online, --force

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/../.."

# Default: force mode for CI/hooks
FORCE_FLAG="--force"

# Parse args
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --json|--strict|--online)
            ARGS+=("$1")
            shift
            ;;
        --no-force)
            FORCE_FLAG=""
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --json      Output JSON"
            echo "  --strict    Block on warnings too"
            echo "  --online    Check external links"
            echo "  --no-force  Skip if not enabled"
            echo "  --help      Show this help"
            exit 0
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Run validation
exec bash "$REPO_ROOT/skills/documentation/resources/verify_documentation.sh" \
    "$REPO_ROOT" \
    $FORCE_FLAG \
    "${ARGS[@]}"
