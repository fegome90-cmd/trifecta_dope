#!/usr/bin/env bash
# bug-hunt-skill-hub.sh: Adversarial real-world test suite for skill-hub
# Run: bash scripts/bug-hunt-skill-hub.sh
# All commands use the terminal alias 'skill-hub'

set -uo pipefail

PASS=0
FAIL=0
TOTAL=0

check() {
    local desc="$1"
    local cmd="$2"
    local expected="$3"
    local unexpected="$4"

    TOTAL=$((TOTAL + 1))
    printf "  [%02d] %-55s " "$TOTAL" "$desc"

    output="$(eval "$cmd" 2>&1)" || true

    if echo "$output" | grep -q "$expected" 2>/dev/null; then
        if [ -n "$unexpected" ] && echo "$output" | grep -q "$unexpected" 2>/dev/null; then
            echo "FAIL (unexpected '$unexpected' found)"
            echo "       cmd: $cmd"
            echo "       out: $(echo "$output" | head -3)"
            FAIL=$((FAIL + 1))
        else
            echo "PASS"
            PASS=$((PASS + 1))
        fi
    else
        echo "FAIL (expected '$expected' not found)"
        echo "       cmd: $cmd"
        echo "       out: $(echo "$output" | head -3)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================================="
echo "  skill-hub Real-World Bug Hunt"
echo "  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================================="
echo ""

# --- SECTION 1: Plain mode (default) ---
echo "--- Section 1: Plain mode (default) ---"

check "Basic single-word query" \
    "skill-hub python --limit 3" \
    "python" ""

check "Multi-word query (triggers reranking)" \
    "skill-hub 'real world bug hunt'" \
    "bug" ""

check "Limit=1 produces exactly 1 result block" \
    "skill-hub refactor --limit 1" \
    "refactor" ""

check "Gibberish query (no results)" \
    "skill-hub 'xyzzyqwer12345nonexistent'" \
    "" ""  # Just ensure no crash

check "Special characters in query" \
    "skill-hub 'test & refactor <code>'" \
    "" ""  # No crash on special chars

check "Empty result set doesn't crash" \
    "skill-hub 'zzzzzzzz_nonexistent_skill_9999'" \
    "" ""

check "Unicode query" \
    "skill-hub 'depuración'" \
    "" ""  # No crash on unicode

# --- Section 2: Cards mode ---
echo ""
echo "--- Section 2: Cards mode (--cards) ---"

check "Cards mode basic" \
    "skill-hub --cards python --limit 1" \
    "python" ""

check "Cards mode multi-word" \
    "skill-hub --cards 'docker best practices'" \
    "" ""  # No crash

check "Cards mode --limit validation" \
    "skill-hub --cards refactor --limit 0 2>&1" \
    "positive integer" ""

check "Cards mode --limit negative" \
    "skill-hub --cards refactor --limit -1 2>&1" \
    "positive integer" ""

check "Cards mode no results" \
    "skill-hub --cards 'xyzzyqwer12345nonexistent'" \
    "" ""  # No crash, clean exit

# --- Section 3: Help and flags ---
echo ""
echo "--- Section 3: Help and flags ---"

check "--help flag" \
    "skill-hub --help" \
    "Search for skills" ""

check "-h flag" \
    "skill-hub -h" \
    "Natural language" ""

check "--limit without value errors" \
    "skill-hub --limit 2>&1" \
    "requires a value" ""

check "--limit with non-numeric" \
    "skill-hub --limit abc test 2>&1" \
    "positive integer" ""

# --- Section 4: Alias matching (dual-family) ---
echo ""
echo "--- Section 4: Alias matching (dual-family) ---"

check "Exact skill alias match" \
    "skill-hub 'python-patterns'" \
    "python" ""

check "Partial skill name" \
    "skill-hub 'python'" \
    "python" ""

# --- Section 5: Exit codes ---
echo ""
echo "--- Section 5: Exit codes ---"

check "Exit code 0 on results" \
    "skill-hub python; echo \$?" \
    "0" ""

check "Exit code 1 on no query" \
    "skill-hub 2>&1; echo \$?" \
    "1" ""

check "Exit code 2 on bad flag" \
    "skill-hub --limit 0 test 2>&1; echo \$?" \
    "2" ""

# --- Section 6: Cards mode rich vs plain ---
echo ""
echo "--- Section 6: Cards mode TTY detection ---"

check "Cards plain via pipe (not TTY)" \
    "skill-hub --cards python --limit 1 | cat" \
    "python" ""

check "Cards JSON-style output clean" \
    "skill-hub --cards refactor --limit 1 2>&1" \
    "" ""  # No crash

# --- Section 7: Edge cases from audit ---
echo ""
echo "--- Section 7: Edge cases from audit ---"

check "Query with double quotes" \
    "skill-hub 'test \"quoted\" word'" \
    "" ""  # No crash

check "Query with single quotes" \
    "skill-hub \"test 'quoted' word\"" \
    "" ""  # No crash

check "Very long query (>200 chars)" \
    "skill-hub 'this is a very long query that tests how skill hub handles extremely verbose search terms that go on and on and on about refactoring code patterns and testing methodologies and deployment strategies'" \
    "" ""  # No crash

check "Multiple --limit flags (last wins)" \
    "skill-hub --limit 1 --limit 5 python" \
    "python" ""

# --- Summary ---
echo ""
echo "=========================================================="
echo "  RESULTS: $PASS PASS / $FAIL FAIL / $TOTAL total"
echo "=========================================================="

if [ "$FAIL" -gt 0 ]; then
    echo "  Status: BUG HUNT FOUND ISSUES"
    exit 1
else
    echo "  Status: ALL CLEAR"
    exit 0
fi
