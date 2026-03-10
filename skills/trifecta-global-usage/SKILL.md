---
name: trifecta-global-usage
description: Use Trifecta globally from any repository and install it in new projects. Covers alias setup, initialization, daemon management, and context workflows.
version: 1.0.0
source: local-git-analysis
analyzed_commits: 50
---

# Trifecta Global Usage

Complete guide to using Trifecta from any repository with global alias and initializing it in new projects.

## Prerequisites

- Trifecta installed at `~/Developer/agent_h/trifecta_dope`
- `uv` package manager installed
- Fish or Bash shell

## Setup Global Alias

### Fish Shell

```bash
# Create config directory
mkdir -p ~/.config/fish/conf.d

# Add alias
cat > ~/.config/fish/conf.d/trifecta.fish << 'EOF'
# Trifecta CLI alias
alias trifecta="uv --directory ~/Developer/agent_h/trifecta_dope run trifecta"
EOF

# Reload
source ~/.config/fish/conf.d/trifecta.fish
```

### Bash Shell

```bash
# Add to ~/.bashrc
echo 'alias trifecta="uv --directory ~/Developer/agent_h/trifecta_dope run trifecta"' >> ~/.bashrc

# Reload
source ~/.bashrc
```

## Initialize Trifecta in New Repository

### Step 1: Create Segment

```bash
cd /path/to/your/repo

# Option A: Relative path (if cwd is repo)
trifecta create --segment .

# Option B: Absolute path (recommended)
trifecta create --segment /path/to/your/repo
```

**Creates:**
- `AGENTS.md` - Agent instructions
- `skill.md` - Repo-specific skills
- `_ctx/prime_{repo}.md` - Reading list
- `_ctx/agent_{repo}.md` - Technical state
- `_ctx/session_{repo}.md` - Session log
- `_ctx/trifecta_config.json` - Config

### Step 2: Sync Context

```bash
# Build context pack from repo files
trifecta ctx sync --segment /path/to/your/repo
```

**Generates:**
- `_ctx/context_pack.json` - Searchable index
- `_ctx/stubs/repo_map.md` - Repository structure
- `_ctx/stubs/symbols_stub.md` - AST symbols

### Step 3: Verify Installation

```bash
# Validate context pack integrity
trifecta ctx validate --segment /path/to/your/repo

# Test search
trifecta ctx search --segment /path/to/your/repo --query "main function" --limit 5
```

## Common Workflows

### Context Search Workflow

```bash
# 1. Search for relevant context
trifecta ctx search --segment /path/to/repo --query "authentication flow" --limit 6

# 2. Get specific chunks
trifecta ctx get --segment /path/to/repo --ids "repo:abc123,repo:def456" --mode excerpt

# 3. Load full context for task
trifecta load --segment /path/to/repo --mode fullfiles --task "Explain how symbols are extracted"
```

### Daemon Management

```bash
# Start daemon for repo
trifecta daemon start --repo /path/to/repo

# Check status (shows PID if running)
trifecta daemon status --repo /path/to/repo

# Stop daemon
trifecta daemon stop --repo /path/to/repo

# Restart daemon
trifecta daemon restart --repo /path/to/repo
```

**Daemon Protocol (via Unix socket):**
- `PING` → `PONG` (health check)
- `HEALTH` → `{"status":"ok","pid":XXX,"uptime":XXX}`
- `SHUTDOWN` → `OK` (graceful termination)

**Test Protocol:**
```bash
# Find socket path
SOCKET=$(find ~/.local/share/trifecta/repos/*/runtime/daemon/socket | head -1)

# Test PING
echo "PING" | nc -U "$SOCKET"

# Test HEALTH
echo "HEALTH" | nc -U "$SOCKET"

# Test SHUTDOWN
echo "SHUTDOWN" | nc -U "$SOCKET"
```

### Repository Registry

```bash
# Register repository
trifecta repo register /path/to/repo

# List all registered repos
trifecta repo list

# Show repo details
trifecta repo show <repo_id>
```

## Path Handling

### ⚠️ Critical: Absolute vs Relative Paths

**Problem:**
```bash
# ❌ WRONG - Uses current directory, may be wrong repo
cd /some/other/repo
trifecta ctx search --segment . --query "test"
```

**Solution:**
```bash
# ✅ CORRECT - Always use absolute path
trifecta ctx search --segment /path/to/target/repo --query "test"
```

### Canonical Paths

Trifecta uses `Path.resolve()` for canonical paths:
- Symlinks resolved
- `..` normalized
- Relative → absolute

**Example:**
```python
# All these produce the same repo_id:
"/tmp/repo"
"/tmp/link_to_repo"  # symlink
"../tmp/repo"        # relative
"/tmp/repo/subdir/.." # parent reference
```

## Architecture

### Directory Structure

```
~/.local/share/trifecta/
├── repos.db                 # Global registry (schema_version=1)
├── trifecta_repos.json      # Repo metadata
└── repos/
    └── {fingerprint}/
        └── runtime/
            └── daemon/
                ├── socket   # Unix socket
                ├── pid      # Process ID
                └── log      # Daemon log

{repo}/
├── _ctx/
│   ├── context_pack.json    # Search index
│   ├── trifecta_config.json # Config
│   ├── prime_{repo}.md      # Reading list
│   ├── agent_{repo}.md      # Technical state
│   ├── session_{repo}.md    # Session log
│   └── stubs/
│       ├── repo_map.md
│       └── symbols_stub.md
├── AGENTS.md
└── skill.md
```

### Clean Architecture

```
Domain (pure business logic)
    ↓
Application (use cases, orchestration)
    ↓
Infrastructure (CLI, adapters, IO)
```

**Key Components:**
- `src/platform/daemon_manager.py` - Daemon lifecycle
- `src/platform/repo_store.py` - Repo registry, schema versioning
- `src/infrastructure/cli.py` - CLI commands
- `src/application/` - Use cases

## Database Schema

### Schema Versioning (WO-M3)

**Fail-closed semantics:**
- New DB: `schema_version=1`
- Old DB without version: **ERROR** "schema version mismatch: expected 1, got none"
- Wrong version: **ERROR** "schema version mismatch: expected 1, got 2"

**Verification:**
```bash
# Check schema version
sqlite3 ~/.trifecta/repos.db "SELECT * FROM schema_version;"
# Output: 1

# Check integrity
sqlite3 ~/.trifecta/repos.db "PRAGMA integrity_check;"
# Output: ok
```

### SQLite Contention (WO-M4)

**Policy: Option B - Internal Serialization**
- SQLite handles contention via file-level locking
- Writers automatically queued and processed sequentially
- No explicit error on contention
- Final state always consistent

**Characterized with:**
- 10-20 concurrent writers
- On-disk DB (not `:memory:`)
- Kernel-level file locking
- No WAL mode needed

**See:** `docs/adr/adr-sqlite-contention-policy.md`

## Testing

### Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run daemon tests
uv run pytest tests/integration/daemon/ -v

# Run schema versioning tests
uv run pytest tests/integration/test_schema_version.py -v

# Run SQLite contention tests
uv run pytest tests/integration/test_sqlite_contention.py -v
```

### Test Coverage

- **29 integration tests** passing
- **C1-C5 criteria** verified
- **Protocol tests** with netcat
- **Daemon lifecycle** tests

## Troubleshooting

### Issue: "Failed to start daemon"

**Cause:** `daemon run` command not implemented (WO-M0 incomplete)

**Solution:** ✅ Fixed - Protocol implemented with PING/HEALTH/SHUTDOWN

### Issue: "Context pack not found"

**Cause:** `ctx sync` not run or wrong path

**Solution:**
```bash
# Use absolute path
trifecta ctx sync --segment /absolute/path/to/repo
```

### Issue: "Permission denied" on socket

**Cause:** Daemon not running or socket stale

**Solution:**
```bash
# Stop daemon (cleans socket)
trifecta daemon stop --repo /path/to/repo

# Start fresh
trifecta daemon start --repo /path/to/repo
```

### Issue: "schema version mismatch"

**Cause:** DB created with different schema version

**Solution:**
- **New repo:** Delete `~/.trifecta/repos.db` and re-register
- **Old repo:** Migrate schema (not implemented yet)

## Constraints

- **Clean Architecture:** domain → application → infrastructure
- **No type suppression:** Never use `as any`, `@ts-ignore`
- **TDD:** Write tests before implementation
- **Simple daemon:** No over-engineering
- **On-disk DB:** For contention tests (file locking is kernel-level)

## Related Skills

- `wo/wo/create` - Create Work Orders
- `wo/wo/take` - Take WO with worktree
- `wo/wo/finish` - Complete WO with validation
- `ctx-md-sync` - Sync context pack

## Quick Reference

```bash
# Setup alias (once)
echo 'alias trifecta="uv --directory ~/Developer/agent_h/trifecta_dope run trifecta"' >> ~/.bashrc
source ~/.bashrc

# Initialize in new repo
cd /path/to/repo
trifecta create --segment $(pwd)
trifecta ctx sync --segment $(pwd)
trifecta ctx validate --segment $(pwd)

# Search context
trifecta ctx search --segment $(pwd) --query "authentication" --limit 5

# Daemon lifecycle
trifecta daemon start --repo $(pwd)
trifecta daemon status --repo $(pwd)
trifecta daemon stop --repo $(pwd)

# Test daemon protocol
SOCKET=$(find ~/.local/share/trifecta/repos/*/runtime/daemon/socket | head -1)
echo "PING" | nc -U "$SOCKET"
echo "HEALTH" | nc -U "$SOCKET"
```

## Verification Criteria

✅ **C1:** Daemon start/status/stop with OS-verifiable PID
✅ **C2:** Path canonicalization with duplicate detection
✅ **C3:** 3-repo smoke isolation
✅ **C4:** Schema version fail-closed
✅ **C5:** SQLite contention characterization

## References

- Plan: `.sisyphus/plans/e-v1-runtime-maturity-plan.md`
- ADR: `docs/adr/adr-sqlite-contention-policy.md`
- Tests: `tests/integration/`
- Checkpoint: `_ctx/checkpoints/2026-03-06/checkpoint_192634_e-v1-runtime-maturity-complete.md`
