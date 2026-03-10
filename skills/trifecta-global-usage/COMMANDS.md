# Trifecta Global Commands

Quick reference for using Trifecta globally from any repository.

## Setup (One-Time)

```bash
# Fish shell
source ~/.config/fish/conf.d/trifecta.fish
source ~/.config/fish/conf.d/trifecta-init.fish
source ~/.config/fish/conf.d/trifecta-commands.fish

# Bash shell
source ~/.bashrc
```

## Main Commands

### Initialize Trifecta in New Repo

```bash
# Current directory
trifecta-init

# Specific directory
trifecta-init /path/to/repo
```

**What it does:**
1. Creates segment (`trifecta create`)
2. Syncs context (`trifecta ctx sync`)
3. Validates (`trifecta ctx validate`)

### Show Help/Skill

```bash
# Show QUICKSTART guide
trifecta-help
```

## Short Commands

### Context Operations

```bash
# Search (current repo)
tsearch "authentication"

# Sync (current repo)
tsync
```

### Daemon Operations

```bash
# Start daemon
tstart

# Check status
tstatus

# Stop daemon
tstop
```

## Full Trifecta Commands

```bash
# Context search with full options
trifecta ctx search --segment $(pwd) --query "auth" --limit 10

# Get specific chunks
trifecta ctx get --segment $(pwd) --ids "repo:abc123,repo:def456" --mode excerpt

# Validate context
trifecta ctx validate --segment $(pwd)

# Daemon lifecycle
trifecta daemon start --repo $(pwd)
trifecta daemon status --repo $(pwd)
trifecta daemon stop --repo $(pwd)
trifecta daemon restart --repo $(pwd)

# Repository registry
trifecta repo register /path/to/repo
trifecta repo list
trifecta repo show <repo_id>
```

## Protocol Testing

```bash
# Find daemon socket
SOCKET=$(find ~/.local/share/trifecta/repos/*/runtime/daemon/socket | head -1)

# Test PING
echo "PING" | nc -U "$SOCKET"
# Expected: PONG

# Test HEALTH
echo "HEALTH" | nc -U "$SOCKET"
# Expected: {"status":"ok","pid":XXX,"uptime":XXX,"version":"1.0.0"}

# Test SHUTDOWN
echo "SHUTDOWN" | nc -U "$SOCKET"
# Expected: OK
```

## Skill-Hub Search

```bash
# Find skill
skill-hub "trifecta global install setup"

# Find daemon info
skill-hub "daemon start stop status"

# Find context workflows
skill-hub "context search workflow"
```

## Architecture

```
~/.config/fish/conf.d/
├── trifecta.fish           # Main alias
├── trifecta-init.fish      # Init + help functions
└── trifecta-commands.fish  # Short commands

~/Developer/agent_h/trifecta_dope/skills/trifecta-global-usage/
├── SKILL.md               # Full skill (9.1 KB)
└── QUICKSTART.md          # Quick reference (2.7 KB)

~/.trifecta/segments/skills-hub/
└── trifecta-global-usage.md  # Indexed globally
```

## Troubleshooting

### Command not found

```bash
# Reload fish
source ~/.config/fish/config.fish

# Or manually
source ~/.config/fish/conf.d/trifecta.fish
source ~/.config/fish/conf.d/trifecta-init.fish
source ~/.config/fish/conf.d/trifecta-commands.fish
```

### Context pack not found

```bash
# Use absolute path
trifecta ctx sync --segment /absolute/path/to/repo
```

### Daemon not responding

```bash
# Stop and restart
tstop
tstart

# Check socket
ls -la ~/.local/share/trifecta/repos/*/runtime/daemon/socket
```

## Examples

### Example 1: New Project Setup

```bash
cd ~/Developer/my-new-project
trifecta-init
tsearch "main function"
```

### Example 2: Search Existing Repo

```bash
cd ~/Developer/existing-project
tsearch "authentication flow"
tsearch "database schema"
tstart
```

### Example 3: Multi-Repo Workflow

```bash
# Register multiple repos
trifecta repo register ~/Developer/project-a
trifecta repo register ~/Developer/project-b

# List all
trifecta repo list

# Start daemon in both
cd ~/Developer/project-a && tstart
cd ~/Developer/project-b && tstart
```

## Related Skills

- `trifecta-global-usage` - Full documentation
- `wo/wo/create` - Create Work Orders
- `wo/wo/take` - Take WO with worktree
- `wo/wo/finish` - Complete WO with validation

## Version

- **Skill:** trifecta-global-usage v1.0.0
- **Commands:** v1.0.0
- **Last Updated:** 2026-03-06

## Feedback

Found a bug or have a suggestion? Create an issue in:
- `~/Developer/agent_h/trifecta_dope`
- GitHub: fegome90-cmd/trifecta_dope
