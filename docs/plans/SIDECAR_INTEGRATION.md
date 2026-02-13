# Sidecar ↔ Trifecta Integration

**Status**: ✅ Fully automatic - WO changes trigger index updates, Sidecar reads automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Trifecta CLI                                  │
│                      (Python project)                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ 1. Take/Finish WO
                                   │    → Hook: regenerate JSON index
                                   ↓
                        ┌──────────────────────────────────────────┐
                        │ _ctx/index/wo_worktrees.json │  ← Generated
                        └──────────────────────────────────────────┘
                                   │
                                   │ 2. Sidecar reads on Init()
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Sidecar (Go)                                    │
│                      internal/plugins/trifecta/                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Contract

**File**: `_ctx/index/wo_worktrees.json`

```json
{
  "version": 1,
  "schema": "trifecta.sidecar.wo_index.v1",
  "generated_at": "2026-02-11T19:33:54+00:00",
  "repo_root": "/Users/felipe/.../trifecta_dope",
  "git_head_sha_repo_root": "59a0807...",
  "work_orders": [
    {
      "id": "WO-0017",
      "title": "CLI trifecta ctx discover Command",
      "status": "pending",
      "priority": "P2",
      "owner": null,
      "epic_id": "",
      "worktree_path": "../.worktrees/WO-0017",
      "worktree_exists": false,
      "branch": "feat/wo-WO-0017",
      "worktree_head_sha": null,
      "wo_yaml_path": "_ctx/jobs/pending/WO-0017.yaml",
      "created_at": "",
      "closed_at": null
    }
  ],
  "errors": []
}
```

**Key invariants**:
- `repo_root`: Absolute path to Trifecta project
- `worktree_path`: Relative to `repo_root` (uses `../` for external worktrees)
- `wo_yaml_path`: Relative to `repo_root`

---

## Automatic Flow

### Step 1: Take WO (regenerates index)

```bash
cd /Users/felipe/.../trifecta_dope
trifecta take WO-0017
```

**What happens**:
1. WO moves to `_ctx/jobs/running/WO-0017.yaml`
2. Hook executes `python scripts/export_wo_index.py`
3. JSON updated at `_ctx/index/wo_worktrees.json`
4. WO status → `"running"`

### Step 2: Finish WO (regenerates index)

```bash
trifecta finish WO-0017 --result done
```

**What happens**:
1. WO moves to `_ctx/jobs/done/WO-0017.yaml`
2. Hook executes `python scripts/export_wo_index.py`
3. JSON updated at `_ctx/index/wo_worktrees.json`
4. WO status → `"done"`

### Step 3: View in Sidecar (reads index)

```bash
cd /tmp/sidecar
./bin/sidecar -project /Users/felipe/.../trifecta_dope
```

**What happens**:
1. Sidecar plugin calls `Init(ctx *plugin.Context)`
2. `loadIndex()` reads `<WorkDir>/_ctx/index/wo_worktrees.json`
3. JSON validated against schema `trifecta.sidecar.wo_index.v1`
4. WOs displayed with filters

**No manual copy needed** - Sidecar reads directly from Trifecta project directory.

---

## Sidecar Keybindings

| Key | Action | Description |
|-----|--------|-------------|
| `R` | Refresh | Reload JSON index |
| `r` | Filter running | Show only running WOs |
| `p` | Filter pending | Show only pending WOs |
| `d` | Filter done | Show only done WOs |
| `f` | Filter failed | Show only failed WOs |
| `a` | Show all | Clear filter |
| `Enter` | Details | Show WO details |
| `o` | YAML path | Log YAML file path |
| `↑↓` or `kj` | Navigate | Move cursor up/down |
| `q` or `Esc` | Quit | Exit Sidecar |

---

## Plugin Implementation

**Files** (`/tmp/sidecar/internal/plugins/trifecta/`):

```
trifecta/
├── plugin.go      # Main plugin (update, view, keybindings)
└── types.go       # WOIndex, WorkOrder, WOStatus types
```

**Registration** (`cmd/sidecar/main.go`):
```go
import "github.com/marcus/sidecar/internal/plugins/trifecta"

// Register Trifecta plugin
if err := registry.Register(trifecta.New()); err != nil {
    logger.Warn("failed to register trifecta plugin", "err", err)
}
```

**Index path resolution**:
```go
func (p *Plugin) IndexFilePath() string {
    // p.ctx.WorkDir = -project argument value
    return filepath.Join(p.ctx.WorkDir, "_ctx", "index", IndexFilename)
}
```

---

## Build & Run Sidecar

```bash
# Clone/build Sidecar (one-time setup)
cd /tmp/sidecar
make build  # Uses CGO_ENABLED=0 for Nix compatibility

# Run with Trifecta project
./bin/sidecar -project /Users/felipe/Developer/agent_h/trifecta_dope
```

**Or create alias**:
```bash
# Add to ~/.zshrc or ~/.bashrc
alias sidecar='cd /tmp/sidecar && ./bin/sidecar -project /Users/felipe/Developer/agent_h/trifecta_dope'
```

---

## Troubleshooting

### Sidecar shows "Error: File not found"

**Cause**: `_ctx/index/wo_worktrees.json` doesn't exist

**Fix**:
```bash
cd /Users/felipe/.../trifecta_dope
python scripts/export_wo_index.py
```

### Sidecar shows "Error: Schema error"

**Cause**: JSON version mismatch or corrupt file

**Fix**:
```bash
# Regenerate index
cd /Users/felipe/.../trifecta_dope
python scripts/export_wo_index.py
```

### Index shows stale data

**Cause**: Sidecar loaded index before WO change

**Fix**: Press `R` in Sidecar to refresh

### Build fails on Nix

**Cause**: Nix-managed Go toolchain linker issue

**Fix** (already in Makefile):
```makefile
build:
	CGO_ENABLED=0 go build -o bin/sidecar ./cmd/sidecar
```

---

## Development Status

| Component | Status | Location |
|-----------|--------|----------|
| Trifecta export script | ✅ Done | `scripts/export_wo_index.py` |
| Hooks (take/finish) | ✅ Done | `scripts/ctx_wo_take.py`, `scripts/ctx_wo_finish.py` |
| JSON index generation | ✅ Done | `_ctx/index/wo_worktrees.json` |
| Sidecar Go plugin | ✅ Done | `/tmp/sidecar/internal/plugins/trifecta/` |
| Build system | ✅ Done | `/tmp/sidecar/Makefile` (CGO_ENABLED=0) |
| **Integration** | **✅ Automatic** | No manual steps required |

---

## Next Steps (Optional Enhancements)

1. **Auto-refresh**: Poll for index changes every N seconds
2. **Real editor**: Import tmux editor for `o` key (currently logs only)
3. **Filter by owner**: Add `u` key to filter by WO owner
4. **Sort options**: Add `s` key to cycle sort (id/status/priority)
5. **WO creation**: Add `c` key to create new WO from Sidecar

---

**Last updated**: 2026-02-11
