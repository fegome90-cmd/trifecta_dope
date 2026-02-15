#!/bin/bash
# verify_documentation.sh — validates documentation patterns with signals
# Flags: --online, --json, --strict, --force
# Enable: .documentation-skill.enabled or DOCS_SKILL_ENABLED=1
# Signals: ownership, adr, coverage-lite (opt-in via config)

set -uo pipefail

REPO_ROOT="${1:-.}"
ERRORS=0
WARNINGS=0
PASSES=0
INFOS=0
SKIPS=0
ONLINE_MODE=false
JSON_MODE=false
STRICT_MODE=false

# Config
OWNERSHIP_REQUIRED="${OWNERSHIP_REQUIRED:-0}"
ADR_REQUIRED="${ADR_REQUIRED:-0}"
COVERAGE_MODE="${COVERAGE_MODE:-lite}"
SRC_DIRS="${SRC_DIRS:-src,lib}"
DOC_DIRS="${DOC_DIRS:-docs}"
EXCLUDED_DIRS="__pycache__,.git,node_modules,dist,build,.venv,venv,_build"

while [[ $# -gt 0 ]]; do
    case $1 in
        --online)  ONLINE_MODE=true;  shift ;;
        --json)    JSON_MODE=true;    shift ;;
        --strict)  STRICT_MODE=true;  shift ;;
        --force)   SKIP_IF_DISABLED=true; shift ;;
        *)         [[ "$1" != "--"* ]] && REPO_ROOT="$1"; shift ;;
    esac
done

# WO Prohibition Guard
WO_PATTERNS="_ctx/ _ctx/jobs/ _ctx/backlog/ WO- backlog.yaml"
is_wo_path() {
    local path="$1"
    for pat in $WO_PATTERNS; do
        [[ "$path" == *"$pat"* ]] && return 0
    done
    return 1
}

check_enabled() {
    [[ "${SKIP_IF_DISABLED:-}" == "true" ]] && return 0
    [[ "${DOCS_SKILL_ENABLED:-}" == "1" ]] && return 0
    [[ -f "$REPO_ROOT/.documentation-skill.enabled" ]] && return 0
    [[ -f "$REPO_ROOT/.documentation-skill" ]] && return 2
    return 1
}

check_enabled
case $? in
    0)  ;;
    2)  [[ "$JSON_MODE" == "true" ]] && echo '{"status": "SKIP", "reason": "deprecated sentinel"}' || \
            echo "⚠️  WARN: .documentation-skill deprecated, use .documentation-skill.enabled" ;;
    *)  [[ "$JSON_MODE" == "true" ]] && echo '{"status": "SKIP", "reason": "not enabled"}' || \
            echo "ℹ️  SKIP: Documentation skill not enabled"
        echo "      Enable: touch .documentation-skill.enabled or DOCS_SKILL_ENABLED=1"
        exit 0 ;;
esac

CORE_ERRORS=0
CORE_WARNINGS=0
OVERMIND_ERRORS=0
OVERMIND_WARNINGS=0

output_pass() { PASSES=$((PASSES + 1)); [[ "$JSON_MODE" == "true" ]] && echo "{\"status\": \"PASS\", \"check\": \"$1\", \"message\": \"$2\"}" || echo "[✓] PASS: $2"; }
output_warn() { 
    WARNINGS=$((WARNINGS + 1)); 
    [[ "$1" == "ownership" || "$1" == "adr" || "$1" == "coverage" ]] && OVERMIND_WARNINGS=$((OVERMIND_WARNINGS + 1)) || CORE_WARNINGS=$((CORE_WARNINGS + 1))
    [[ "$JSON_MODE" == "true" ]] && echo "{\"status\": \"WARN\", \"check\": \"$1\", \"message\": \"$2\"}" || echo "[⚠] WARN: $2"; 
}
output_fail() { 
    ERRORS=$((ERRORS + 1)); 
    [[ "$1" == "ownership" || "$1" == "adr" || "$1" == "coverage" ]] && OVERMIND_ERRORS=$((OVERMIND_ERRORS + 1)) || CORE_ERRORS=$((CORE_ERRORS + 1))
    [[ "$JSON_MODE" == "true" ]] && echo "{\"status\": \"FAIL\", \"check\": \"$1\", \"message\": \"$2\"}" || echo "[✗] FAIL: $2"; 
}
output_info() { INFOS=$((INFOS + 1));   [[ "$JSON_MODE" == "true" ]] && echo "{\"status\": \"INFO\", \"check\": \"$1\", \"message\": \"$2\"}" || echo "[ℹ] INFO: $2"; }
output_skip() { SKIPS=$((SKIPS + 1));   [[ "$JSON_MODE" == "true" ]] && echo "{\"status\": \"SKIP\", \"check\": \"$1\", \"message\": \"$2\"}" || echo "[→] SKIP: $2"; }

check_file() {
    [[ -f "$REPO_ROOT/$1" ]] && output_pass "file_exists" "$1 exists" || output_fail "file_exists" "$1 not found"
}

check_critical() {
    grep -q "## ⚠️ CRITICAL" "$REPO_ROOT/$1" 2>/dev/null && output_pass "critical_section" "CRITICAL section found" || output_fail "critical_section" "$1 missing CRITICAL section"
}

check_proceed() {
    grep -q "DO NOT PROCEED" "$REPO_ROOT/$1" 2>/dev/null && output_pass "proceed_phrase" "DO NOT PROCEED found" || output_fail "proceed_phrase" "$1 missing DO NOT PROCEED"
}

check_mandatory() {
    local count
    count=$(grep -cE "← START HERE|← THEN READ|← REFERENCE" "$REPO_ROOT/$1" 2>/dev/null || true)
    count=${count:-0}
    [[ "$count" -lt 3 ]] && output_fail "mandatory_files" "fewer than 3 mandatory files (found: $count)" || \
    [[ "$count" -gt 5 ]] && output_warn "mandatory_files" "more than 5 mandatory files ($count)" || \
    output_pass "mandatory_files" "$count mandatory files (within range)"
}

check_time_est() {
    grep -qE "\([0-9]+ min" "$REPO_ROOT/$1" 2>/dev/null && output_pass "time_estimates" "Time estimates present" || output_fail "time_estimates" "Missing time estimates"
}

check_skip_section() {
    grep -q "If You Skip" "$REPO_ROOT/$1" 2>/dev/null && output_pass "skip_section" "If You Skip found" || output_fail "skip_section" "Missing If You Skip"
}

check_consequences() {
    grep -q "Skip this → you'll" "$REPO_ROOT/$1" 2>/dev/null && output_pass "consequences" "Consequences specified" || output_fail "consequences" "Missing consequences"
}

check_no_absolute() {
    grep -qE "(/Users/|/home/|C:\\\\Users|/opt/)|^/[a-z]+/" "$REPO_ROOT/$1" 2>/dev/null && output_fail "absolute_paths" "Contains absolute paths" || output_pass "absolute_paths" "No absolute paths"
}

check_local_links() {
    local broken=0
    while IFS= read -r link; do
        [[ -z "$link" ]] && continue
        [[ "$link" =~ ^https?:// ]] && continue
        [[ "$link" =~ ^# ]] && continue
        is_wo_path "$link" && continue
        [[ ! -f "$REPO_ROOT/$link" ]] && ((broken++))
    done < <(grep -oP '\[.*?\]\(\K[^)]+' "$REPO_ROOT/$1" 2>/dev/null || true)
    [[ $broken -gt 0 ]] && output_fail "local_links" "$broken broken links" || output_pass "local_links" "All local links valid"
}

check_external_links() {
    [[ "$ONLINE_MODE" != "true" ]] && output_pass "external_links" "Skipped (use --online)" && return
    local broken=0 timeout=5
    while IFS= read -r url; do
        [[ -z "$url" ]] && continue
        [[ ! "$url" =~ ^https?:// ]] && continue
        timeout "$timeout" curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null | grep -q "200\|301\|302" || ((broken++))
    done < <(grep -oP '\[.*?\]\(\Khttps?://[^)]+' "$REPO_ROOT/$1" 2>/dev/null || true)
    [[ $broken -gt 0 ]] && output_warn "external_links" "$broken unreachable links" || output_pass "external_links" "All external links reachable"
}

check_critical_position() {
    local crit_line=$(grep -n "## ⚠️ CRITICAL" "$REPO_ROOT/$1" 2>/dev/null | cut -d: -f1 | head -1 || true)
    local qs_line=$(grep -n "^## Quick Start" "$REPO_ROOT/$1" 2>/dev/null | cut -d: -f1 | head -1 || true)
    [[ -n "$crit_line" && -n "$qs_line" && $crit_line -gt $qs_line ]] && output_fail "critical_position" "CRITICAL after Quick Start" || output_pass "critical_position" "CRITICAL properly positioned"
}

check_staleness() {
    [[ -d "$REPO_ROOT/.git" ]] || { output_warn "staleness" "No git, cannot check"; return; }
    local last_commit_time
    last_commit_time=$(git -C "$REPO_ROOT" log -1 --format=%ct -- "$1" 2>/dev/null || echo "0")
    [[ "$last_commit_time" == "0" || -z "$last_commit_time" ]] && { output_warn "staleness" "No commit history"; return; }
    local age_days=$(( ($(date +%s) - last_commit_time) / 86400 ))
    [[ $age_days -gt 90 ]] && output_warn "staleness" "$age_days days old (recommend refresh)" || \
    [[ $age_days -gt 60 ]] && output_warn "staleness" "$age_days days old (consider refresh)" || \
    output_pass "staleness" "Recently updated ($age_days days)"
}

check_ctx_refs() {
    local missing=0
    while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        [[ "$ref" =~ ^_ctx/ ]] && [[ ! -e "$REPO_ROOT/$ref" ]] && ((missing++))
    done < <(grep -oP '_ctx/[^]\)]+' "$REPO_ROOT/$1" 2>/dev/null || true)
    [[ $missing -gt 0 ]] && output_fail "ctx_references" "$missing _ctx/ refs don't exist" || output_pass "ctx_references" "All _ctx/ references valid"
}

check_sync() {
    [[ ! -f "$REPO_ROOT/CLAUDE.md" || ! -f "$REPO_ROOT/agents.md" ]] && return
    local f1 f2
    f1=$(grep -oP '(?<=\*\*\[)[^]]+' "$REPO_ROOT/CLAUDE.md" 2>/dev/null | sort || true)
    f2=$(grep -oP '(?<=\*\*\[)[^]]+' "$REPO_ROOT/agents.md" 2>/dev/null | sort || true)
    [[ "$f1" != "$f2" ]] && output_warn "synchronization" "Files out of sync" || output_pass "synchronization" "Files synchronized"
}

check_ownership() {
    [[ "$OWNERSHIP_REQUIRED" != "1" ]] && output_skip "ownership" "Not activated (OWNERSHIP_REQUIRED=0)" && return
    
    local codeowners_file="$REPO_ROOT/.github/CODEOWNERS"
    local uncovered=0
    local covered=0
    local uncovered_docs=()
    local docs=()
    
    while IFS= read -r doc; do
        [[ -z "$doc" ]] && continue
        is_wo_path "$doc" && continue
        docs+=("$doc")
    done < <(find "$REPO_ROOT" -maxdepth 1 -name "*.md" -type f 2>/dev/null || true)
    
    [[ ${#docs[@]} -eq 0 ]] && output_info "ownership" "No docs found" && return
    
    local has_codeowners=false
    [[ -f "$codeowners_file" ]] && has_codeowners=true
    
    for doc in "${docs[@]}"; do
        local doc_name
        doc_name=$(basename "$doc")
        local has_owner=false
        
        if $has_codeowners; then
            local line
            while IFS= read -r line; do
                [[ -z "$line" ]] && continue
                [[ "$line" =~ ^# ]] && continue
                if [[ "$line" =~ [^#]*[[:space:]]"$doc_name" ]]; then
                    has_owner=true
                    break
                fi
            done < "$codeowners_file"
        fi
        
        if ! $has_owner; then
            local frontmatter_owner
            frontmatter_owner=$(sed -n '/^---/,/^---/{/^owner:/p}' "$doc" 2>/dev/null | head -1)
            [[ -n "$frontmatter_owner" ]] && has_owner=true
        fi
        
        if $has_owner; then
            ((covered++))
        else
            ((uncovered++))
            uncovered_docs+=("$doc_name")
        fi
    done
    
    local total=$((covered + uncovered))
    [[ $total -eq 0 ]] && output_info "ownership" "No docs to check" && return
    
    if [[ $uncovered -gt 0 ]]; then
        local doc_list
        doc_list=$(printf '%s, ' "${uncovered_docs[@]}" | sed 's/, $//')
        output_warn "ownership" "$uncovered docs without owner (covered: $covered/$total) | Add CODEOWNERS rule or frontmatter 'owner: @team'"
    else
        output_pass "ownership" "All $total docs have owner"
    fi
}

check_adr() {
    local adr_dirs="docs/adr docs/decisions"
    local adr_dir=""
    
    for d in $adr_dirs; do
        [[ -d "$REPO_ROOT/$d" ]] && adr_dir="$d" && break
    done
    
    if [[ -z "$adr_dir" ]]; then
        if [[ "$ADR_REQUIRED" == "1" ]]; then
            output_fail "adr" "ADR_REQUIRED but no docs/adr/ or docs/decisions/ | Create: mkdir docs/adr && echo '# ADRs' > docs/adr/README.md"
        else
            output_skip "adr" "No ADR directory found (set ADR_REQUIRED=1 to enable)"
        fi
        return
    fi
    
    local adr_count=0
    local has_index=false
    
    [[ -f "$REPO_ROOT/$adr_dir/README.md" ]] && has_index=true
    [[ -f "$REPO_ROOT/$adr_dir/index.md" ]] && has_index=true
    
    adr_count=$(find "$REPO_ROOT/$adr_dir" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l || echo 0)
    [[ $adr_count -eq 0 ]] && output_warn "adr" "No ADRs found in $adr_dir | Add ADRs or remove dir" && return
    
    if [[ "$has_index" == "false" ]]; then
        output_warn "adr" "$adr_count ADRs but no index | Add README.md or index.md in $adr_dir"
        return
    fi
    
    local latest_time=0
    [[ -d "$REPO_ROOT/.git" ]] && latest_time=$(git -C "$REPO_ROOT" log -1 --format=%ct -- "$adr_dir" 2>/dev/null || echo "0")
    
    if [[ "$latest_time" == "0" || -z "$latest_time" ]]; then
        output_info "adr" "$adr_count ADRs found, cannot determine staleness (no git history)"
        return
    fi
    
    local age_days=$(( ($(date +%s) - latest_time) / 86400 ))
    [[ $age_days -gt 180 ]] && output_warn "adr" "$adr_count ADRs, latest is $age_days days old (stale) | Review/update ADRs" || \
        output_pass "adr" "$adr_count ADRs, latest is $age_days days old"
}

check_coverage() {
    [[ "$COVERAGE_MODE" == "off" ]] && output_skip "coverage" "Disabled (COVERAGE_MODE=off)" && return
    
    local src_count=0 doc_count=0
    local excluded_dirs="__pycache__ node_modules .git dist build .venv venv _build"
    local src_dirs_used=""
    local doc_dirs_used=""
    
    IFS=',' read -ra SRC_DIRS_ARRAY <<< "$SRC_DIRS"
    for dir in "${SRC_DIRS_ARRAY[@]}"; do
        [[ -d "$REPO_ROOT/$dir" ]] || continue
        [[ -n "$src_dirs_used" ]] && src_dirs_used+=","
        src_dirs_used+="$dir"
        local count
        count=$(find "$REPO_ROOT/$dir" -type f ! -path "*/$excluded_dirs/*" ! -name "*.pyc" 2>/dev/null | wc -l || echo 0)
        src_count=$((src_count + count))
    done
    
    [[ $src_count -eq 0 ]] && output_info "coverage" "No source files (SRC_DIRS=$SRC_DIRS) | Adjust SRC_DIRS config" && return
    
    local meta_docs="LICENSE LICENSE.md CODE_OF_CONDUCT CONTRIBUTING CHANGELOG"
    
    IFS=',' read -ra DOC_DIRS_ARRAY <<< "$DOC_DIRS"
    for dir in "${DOC_DIRS_ARRAY[@]}"; do
        [[ -d "$REPO_ROOT/$dir" ]] || continue
        [[ -n "$doc_dirs_used" ]] && doc_dirs_used+=","
        doc_dirs_used+="$dir"
        while IFS= read -r doc; do
            [[ -z "$doc" ]] && continue
            local name
            name=$(basename "$doc" .md)
            local is_meta=false
            for m in $meta_docs; do
                [[ "$name" == *"$m"* ]] && is_meta=true && break
            done
            $is_meta && continue
            local size
            size=$(stat -f%z "$doc" 2>/dev/null || stat -c%s "$doc" 2>/dev/null || echo 0)
            [[ $size -lt 100 ]] && continue
            local has_content
            has_content=$(grep -cE "^#+ |\\[.*\\]\\(" "$doc" 2>/dev/null | tr -d '\n' || echo "0")
            [[ -n "$has_content" && "$has_content" -gt 0 ]] && doc_count=$((doc_count + 1))
        done < <(find "$REPO_ROOT/$dir" -type f -name "*.md" ! -path "*/$excluded_dirs/*" 2>/dev/null || true)
    done
    
    [[ $doc_count -eq 0 ]] && output_info "coverage" "No valid docs (src=$src_count in $src_dirs_used) | Add docs with >100 chars + heading/link" && return
    
    local ratio
    ratio=$(echo "scale=2; $doc_count / $src_count" | bc 2>/dev/null || echo "0")
    local ratio_int
    ratio_int=$(echo "$ratio * 100" | bc 2>/dev/null | cut -d. -f1 || echo 0)
    local debug_info="src_dirs=$src_dirs_used,doc_dirs=$doc_dirs_used,excluded=$EXCLUDED_DIRS"
    
    [[ $ratio_int -lt 5 ]] && output_warn "coverage" "$doc_count docs / $src_count src = 0.${ratio_int} ratio (CRITICAL) | $debug_info" && return
    [[ $ratio_int -lt 10 ]] && output_info "coverage" "$doc_count docs / $src_count src = 0.${ratio_int} ratio (low) | $debug_info" && return
    output_pass "coverage" "$doc_count docs / $src_count src = 0.${ratio_int} ratio | $debug_info"
}

validate_file() {
    check_file "$1"
    check_critical "$1"
    check_proceed "$1"
    check_mandatory "$1"
    check_time_est "$1"
    check_skip_section "$1"
    check_consequences "$1"
    check_no_absolute "$1"
    check_local_links "$1"
    check_external_links "$1"
    check_critical_position "$1"
    check_staleness "$1"
    check_ctx_refs "$1"
}

[[ "$JSON_MODE" != "true" ]] && echo "🔍 Validating Agent Documentation Pattern..." && echo ""

if [[ -f "$REPO_ROOT/CLAUDE.md" ]]; then
    [[ "$JSON_MODE" != "true" ]] && echo "Checking CLAUDE.md..."
    validate_file "CLAUDE.md"
    [[ "$JSON_MODE" != "true" ]] && echo ""
fi

if [[ -f "$REPO_ROOT/agents.md" ]]; then
    [[ "$JSON_MODE" != "true" ]] && echo "Checking agents.md..."
    validate_file "agents.md"
    [[ "$JSON_MODE" != "true" ]] && echo ""
fi

if [[ -f "$REPO_ROOT/CLAUDE.md" && -f "$REPO_ROOT/agents.md" ]]; then
    [[ "$JSON_MODE" != "true" ]] && echo "Checking synchronization..."
    check_sync
    [[ "$JSON_MODE" != "true" ]] && echo ""
fi

[[ "$JSON_MODE" != "true" ]] && echo "Running signals..."
check_ownership
check_adr
check_coverage
[[ "$JSON_MODE" != "true" ]] && echo ""

SCORE_RAW=$((100 - (ERRORS * 15) - (WARNINGS * 5)))
SCORE=$SCORE_RAW
[[ $SCORE -lt 5 ]] && SCORE=5
[[ $SCORE -gt 100 ]] && SCORE=100

if [[ "$JSON_MODE" == "true" ]]; then
    verdict_block="false"
    [[ $ERRORS -gt 0 || ( "$STRICT_MODE" == "true" && $WARNINGS -gt 0 ) ]] && verdict_block="true"
    echo "{\"schema_version\": \"1.0\", \"score_raw\": $SCORE_RAW, \"score_clamped\": $SCORE, \"verdict\": {\"block\": $verdict_block, \"reason_counts\": {\"fail\": $ERRORS, \"warn\": $WARNINGS}}, \"counts\": {\"pass\": $PASSES, \"warn\": $WARNINGS, \"fail\": $ERRORS, \"info\": $INFOS, \"skip\": $SKIPS}, \"breakdown\": {\"core_errors\": $CORE_ERRORS, \"core_warnings\": $CORE_WARNINGS, \"overmind_errors\": $OVERMIND_ERRORS, \"overmind_warnings\": $OVERMIND_WARNINGS}, \"checks\": []}"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    verdict="ALLOW"
    block_msg=""
    if [[ $ERRORS -gt 0 || ( "$STRICT_MODE" == "true" && $WARNINGS -gt 0 ) ]]; then
        verdict="BLOCK"
        block_msg="($ERRORS FAILs)"
    fi
    
    echo "Gate Verdict: $verdict $block_msg"
    echo "  └─ Core: $CORE_ERRORS FAIL, $CORE_WARNINGS WARN | Overmind: $OVERMIND_ERRORS FAIL, $OVERMIND_WARNINGS WARN"
    echo ""
    echo "Health Score: $SCORE/100 (raw: $SCORE_RAW, clamped to min 5)"
    echo ""
    echo "Summary: $PASSES PASS, $WARNINGS WARN, $ERRORS FAIL, $INFOS INFO, $SKIPS SKIP"
    echo ""
    [[ $ERRORS -gt 0 ]] && echo "❌ BLOCKED: $ERRORS failures" && exit 1
    [[ "$STRICT_MODE" == "true" && $WARNINGS -gt 0 ]] && echo "❌ BLOCKED: strict mode with warnings" && exit 1
    echo "✅ ALLOWED: No blocking failures"
    exit 0
fi
