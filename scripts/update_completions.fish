#!/usr/bin/env fish
# Trifecta Completions Update Checker
# This script checks if completions are outdated and informs the user
# It does NOT modify any files automatically

set SCRIPT_DIR (realpath (dirname (status --current-filename)))
set COMPLETIONS_FILE "$SCRIPT_DIR/../completions/trifecta.fish"
set TRIFECTA_BIN "$SCRIPT_DIR/../src/infrastructure/cli.py"

# Colors
set -g COLOR_RESET (set_color normal)
set -g COLOR_BOLD (set_color --bold)
set -g COLOR_YELLOW (set_color yellow)
set -g COLOR_GREEN (set_color green)
set -g COLOR_RED (set_color red)

echo ""
echo "$COLOR_BOLD=== Trifecta Completions Update Checker ===$COLOR_RESET"
echo ""

# Check if completions file exists
if not test -f "$COMPLETIONS_FILE"
    echo "$COLOR_RED❌ Completions file not found: $COMPLETIONS_FILE$COLOR_RESET"
    echo "   Install completions manually to ~/.config/fish/completions/"
    exit 1
end

# Get commands from CLI help
set -l cli_commands (python3 "$TRIFECTA_BIN" --help 2>/dev/null | grep -oE "^  [a-z-]+" | tr -d ' ' | sort -u)

# Get commands from completions file
set -l completion_commands (grep -oE 'complete -c trifecta.*-a (\w+)' "$COMPLETIONS_FILE" | awk '{print $NF}' | sort -u)

# Check for missing commands
set -l missing_commands
for cmd in $cli_commands
    if not contains -- $cmd $completion_commands
        set -a missing_commands $cmd
    end
end

# Check for extra commands (removed from CLI)
set -l extra_commands
for cmd in $completion_commands
    if not contains -- $cmd $cli_commands
        set -a extra_commands $cmd
    end
end

# Check if lists are empty using count
set -l has_missing (count $missing_commands)
set -l has_extra (count $extra_commands)

# Report results
if test "$has_missing" -eq 0; and test "$has_extra" -eq 0
    echo "$COLOR_GREEN✅ Completions are up to date!$COLOR_RESET"
    echo ""
    echo "Installed at: $COMPLETIONS_FILE"
    echo ""
    echo "To use completions, link to fish completions dir:"
    echo "  ln -s \$COMPLETIONS_FILE ~/.config/fish/completions/trifecta.fish"
else
    echo "$COLOR_YELLOW⚠️  Completions may be outdated$COLOR_RESET"
    echo ""

    if test "$has_missing" -gt 0
        echo "$COLOR_YELLOWMissing commands:$COLOR_RESET"
        for cmd in $missing_commands
            echo "   - $cmd"
        end
        echo ""
    end

    if test "$has_extra" -gt 0
        echo "$COLOR_YELLOWExtra commands (removed from CLI):$COLOR_RESET"
        for cmd in $extra_commands
            echo "   - $cmd"
        end
        echo ""
    end

    echo "$COLOR_BOLDTo update completions:$COLOR_RESET"
    echo "  1. Review: $COMPLETIONS_FILE"
    echo "  2. Compare with: python3 $TRIFECTA_BIN --help"
    echo "  3. Manually update the completions file"
    echo ""
end

exit 0
