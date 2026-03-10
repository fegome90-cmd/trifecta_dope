# Trifecta Global Usage - Quick Start

## Installation (One-Time Setup)

### 1. Configure Alias

**Fish Shell:**
```bash
mkdir -p ~/.config/fish/conf.d
cat > ~/.config/fish/conf.d/trifecta.fish << 'EOF'
alias trifecta="uv --directory ~/Developer/agent_h/trifecta_dope run trifecta"
EOF
```

**Bash Shell:**
```bash
echo 'alias trifecta="uv --directory ~/Developer/agent_h/trifecta_dope run trifecta"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Test Installation

```bash
trifecta --help
```

## Initialize Trifecta in New Repository

```bash
# Navigate to your repository
cd /path/to/your/repo

# Initialize Trifecta
trifecta create --segment $(pwd)

# Build context pack
trifecta ctx sync --segment $(pwd)

# Verify installation
trifecta ctx validate --segment $(pwd)
```

## Common Commands

### Context Operations

```bash
# Search context
trifecta ctx search --segment $(pwd) --query "authentication" --limit 5

# Get specific chunks
trifecta ctx get --segment $(pwd) --ids "repo:abc123" --mode excerpt

# Validate context
trifecta ctx validate --segment $(pwd)
```

### Daemon Management

```bash
# Start daemon
trifecta daemon start --repo $(pwd)

# Check status
trifecta daemon status --repo $(pwd)

# Stop daemon
trifecta daemon stop --repo $(pwd)

# Restart daemon
trifecta daemon restart --repo $(pwd)
```

### Repository Registry

```bash
# Register repository
trifecta repo register /path/to/repo

# List all repos
trifecta repo list

# Show repo details
trifecta repo show <repo_id>
```

## Troubleshooting

### Issue: "command not found: trifecta"

**Solution:** Reload shell or run:
```bash
source ~/.config/fish/conf.d/trifecta.fish  # Fish
source ~/.bashrc                             # Bash
```

### Issue: "Context pack not found"

**Solution:** Run sync with absolute path:
```bash
trifecta ctx sync --segment /absolute/path/to/repo
```

### Issue: "Failed to start daemon"

**Solution:** Ensure daemon protocol is implemented (WO-M0 complete). Check:
```bash
# Test daemon protocol
SOCKET=$(find ~/.local/share/trifecta/repos/*/runtime/daemon/socket | head -1)
echo "PING" | nc -U "$SOCKET"
# Expected: PONG
```

## Find This Skill

```bash
# Search in skill-hub
skill-hub "trifecta global install setup"

# Load directly (from trifecta_dope repo)
skill(name="trifecta-global-usage")
```

## Related Skills

- `wo/wo/create` - Create Work Orders
- `wo/wo/take` - Take WO with worktree
- `wo/wo/finish` - Complete WO with validation

## Full Documentation

See: `skills/trifecta-global-usage/SKILL.md`

## Skill-Hub Location

- **Local:** `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/skills/trifecta-global-usage/`
- **Global:** `~/.trifecta/segments/skills-hub/trifecta-global-usage.md`
