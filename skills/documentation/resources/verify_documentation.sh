#!/bin/bash

# verify_documentation.sh
# Validates that CLAUDE.md and agents.md follow the Agent Documentation skill pattern

set -e

REPO_ROOT="${1:-.}"
ERRORS=0
WARNINGS=0

check_file_exists() {
    local file="$1"
    if [[ ! -f "$REPO_ROOT/$file" ]]; then
        echo "❌ ERROR: File not found: $file"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_section_exists() {
    local file="$1"
    local section="$2"
    if ! grep -q "## ⚠️ CRITICAL" "$REPO_ROOT/$file"; then
        echo "❌ ERROR: $file missing '## ⚠️ CRITICAL' section"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_no_proceeding_phrase() {
    local file="$1"
    if ! grep -q "DO NOT PROCEED" "$REPO_ROOT/$file"; then
        echo "❌ ERROR: $file missing 'DO NOT PROCEED' phrase"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_mandatory_files() {
    local file="$1"
    local count=$(grep -c "← START HERE\|← THEN READ\|← REFERENCE" "$REPO_ROOT/$file" || echo 0)
    if (( count < 3 )); then
        echo "❌ ERROR: $file has fewer than 3 mandatory files (found: $count)"
        ((ERRORS++))
        return 1
    elif (( count > 5 )); then
        echo "⚠️  WARNING: $file has more than 5 mandatory files (found: $count). Consider consolidating."
        ((WARNINGS++))
    fi
    return 0
}

check_time_estimates() {
    local file="$1"
    if ! grep -qE "\([0-9]+ min" "$REPO_ROOT/$file"; then
        echo "❌ ERROR: $file missing time estimates like '(3 min read)'"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_if_you_skip_section() {
    local file="$1"
    if ! grep -q "If You Skip" "$REPO_ROOT/$file"; then
        echo "❌ ERROR: $file missing 'If You Skip' section"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_consequences() {
    local file="$1"
    if ! grep -q "Skip this → you'll" "$REPO_ROOT/$file"; then
        echo "❌ ERROR: $file missing specific consequences (should say 'Skip this → you'll...')"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_no_absolute_paths() {
    local file="$1"
    if grep -qE "(/Users/|/home/|C:\\\\Users|/opt/)|^/[a-z]+/" "$REPO_ROOT/$file"; then
        echo "❌ ERROR: $file contains absolute paths (should use relative paths)"
        ((ERRORS++))
        return 1
    fi
    return 0
}

check_markdown_links() {
    local file="$1"
    local broken_links=$(grep -oP '\[.*?\]\(\K[^)]+' "$REPO_ROOT/$file" | while read link; do
        # Skip http(s) links
        if [[ $link =~ ^https?:// ]]; then
            continue
        fi
        # Check if local file exists
        if [[ ! -f "$REPO_ROOT/$link" ]]; then
            echo "$link"
        fi
    done | wc -l)
    
    if (( broken_links > 0 )); then
        echo "⚠️  WARNING: $file may have broken links (found: $broken_links). Verify manually."
        ((WARNINGS++))
    fi
    return 0
}

check_critical_section_first() {
    local file="$1"
    local critical_line=$(grep -n "## ⚠️ CRITICAL" "$REPO_ROOT/$file" | cut -d: -f1 | head -1)
    local quick_start_line=$(grep -n "^## Quick Start" "$REPO_ROOT/$file" | cut -d: -f1 | head -1)
    
    if [[ ! -z "$critical_line" ]] && [[ ! -z "$quick_start_line" ]]; then
        if (( critical_line > quick_start_line )); then
            echo "❌ ERROR: $file has CRITICAL section after Quick Start (should be FIRST)"
            ((ERRORS++))
            return 1
        fi
    fi
    return 0
}

check_synchronization() {
    local file1="CLAUDE.md"
    local file2="agents.md"
    
    if [[ ! -f "$REPO_ROOT/$file1" ]] || [[ ! -f "$REPO_ROOT/$file2" ]]; then
        return 0  # Skip if one doesn't exist
    fi
    
    # Check if both have same mandatory files
    local files1=$(grep -oP '(?<=\*\*\[)[^]]+' "$REPO_ROOT/$file1" | sort)
    local files2=$(grep -oP '(?<=\*\*\[)[^]]+' "$REPO_ROOT/$file2" | sort)
    
    if [[ "$files1" != "$files2" ]]; then
        echo "⚠️  WARNING: CLAUDE.md and agents.md have different mandatory files list. Keep them in sync!"
        ((WARNINGS++))
    fi
    
    return 0
}

# Main execution
echo "🔍 Validating Agent Documentation Pattern..."
echo ""

# Check CLAUDE.md
if check_file_exists "CLAUDE.md"; then
    echo "Checking CLAUDE.md..."
    check_section_exists "CLAUDE.md"
    check_no_proceeding_phrase "CLAUDE.md"
    check_mandatory_files "CLAUDE.md"
    check_time_estimates "CLAUDE.md"
    check_if_you_skip_section "CLAUDE.md"
    check_consequences "CLAUDE.md"
    check_no_absolute_paths "CLAUDE.md"
    check_markdown_links "CLAUDE.md"
    check_critical_section_first "CLAUDE.md"
    echo "✓ CLAUDE.md checks complete"
    echo ""
fi

# Check agents.md
if check_file_exists "agents.md"; then
    echo "Checking agents.md..."
    check_section_exists "agents.md"
    check_no_proceeding_phrase "agents.md"
    check_mandatory_files "agents.md"
    check_time_estimates "agents.md"
    check_if_you_skip_section "agents.md"
    check_consequences "agents.md"
    check_no_absolute_paths "agents.md"
    check_markdown_links "agents.md"
    check_critical_section_first "agents.md"
    echo "✓ agents.md checks complete"
    echo ""
fi

# Check synchronization
if [[ -f "$REPO_ROOT/CLAUDE.md" ]] && [[ -f "$REPO_ROOT/agents.md" ]]; then
    echo "Checking synchronization between CLAUDE.md and agents.md..."
    check_synchronization
    echo "✓ Synchronization check complete"
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if (( ERRORS == 0 )); then
    echo "✅ All checks PASSED ($WARNINGS warnings)"
    exit 0
else
    echo "❌ FAILED: $ERRORS errors, $WARNINGS warnings"
    exit 1
fi
