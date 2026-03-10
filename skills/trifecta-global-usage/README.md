# Trifecta Global Usage Skill

Complete guide to using Trifecta globally from any repository.

## Files

| File | Size | Purpose |
|------|------|---------|
| `SKILL.md` | 9.1 KB | Full skill with all details |
| `QUICKSTART.md` | 2.7 KB | Quick start guide |
| `COMMANDS.md` | 4.5 KB | Command reference + shortcuts |
| `README.md` | This file | Overview |

## Quick Access

### 1. Search in Skill-Hub

```bash
skill-hub "trifecta global install setup"
```

### 2. Use Fish Functions

```bash
# Initialize in current repo
trifecta-init

# Show quick start
trifecta-help

# Short commands
tsearch "query"    # Search context
tsync              # Sync context
tstart             # Start daemon
tstatus            # Check daemon
tstop              # Stop daemon
```

### 3. Load Skill Directly

```bash
# From trifecta_dope repo
skill(name="trifecta-global-usage")
```

## What's Included

### ✅ Setup Instructions
- Fish shell alias
- Bash shell alias
- One-time configuration

### ✅ Initialization Workflow
- `trifecta-init` command
- Step-by-step guide
- Validation checks

### ✅ Daemon Management
- Start/stop/status/restart
- Protocol documentation (PING/HEALTH/SHUTDOWN)
- Socket testing with netcat

### ✅ Context Operations
- Search workflows
- Get/retrieve chunks
- Validation

### ✅ Architecture Details
- Clean Architecture
- Schema versioning
- SQLite contention (Option B)
- Database schema

### ✅ Troubleshooting
- Common issues + solutions
- Protocol testing
- Socket cleanup

## Installation

### Fish Shell

```bash
# Setup aliases (one-time)
source ~/.config/fish/conf.d/trifecta.fish
source ~/.config/fish/conf.d/trifecta-init.fish
source ~/.config/fish/conf.d/trifecta-commands.fish
```

### Bash Shell

```bash
# Setup alias (one-time)
source ~/.bashrc
```

## Usage Examples

### Initialize New Repo

```bash
cd /path/to/new/repo
trifecta-init
```

### Search Context

```bash
# Short command
tsearch "authentication"

# Full command
trifecta ctx search --segment $(pwd) --query "auth" --limit 10
```

### Daemon Lifecycle

```bash
# Short commands
tstart
tstatus
tstop

# Full commands
trifecta daemon start --repo $(pwd)
trifecta daemon status --repo $(pwd)
trifecta daemon stop --repo $(pwd)
```

## Related Documentation

- **Skill-Hub:** `~/.trifecta/segments/skills-hub/trifecta-global-usage.md`
- **Commands:** `~/.trifecta/segments/skills-hub/trifecta-commands.md`
- **Local:** `~/Developer/agent_h/trifecta_dope/skills/trifecta-global-usage/`

## Version

- **v1.0.0** - Initial release (2026-03-06)
- Analyzed commits: 50
- Integration tests: 29 passing
- Criteria verified: C1-C5

## Feedback

Issues or suggestions? Create an issue in:
- `~/Developer/agent_h/trifecta_dope`
- GitHub: fegome90-cmd/trifecta_dope
