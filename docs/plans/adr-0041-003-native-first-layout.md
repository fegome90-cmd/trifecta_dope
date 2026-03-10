# ADR-0041-003: Native-First Runtime Layout

**Date**: 2026-03-06
**Status**: Proposed
**Epic**: E-V1 (Trifecta V1 Global Platform)
**WO**: WO-0041

## Context

Platform runtime data must be stored in native, platform-appropriate locations:
- Linux: `~/.local/share/trifecta/`
- macOS: `~/Library/Application Support/trifecta/`
- Windows: `%APPDATA%/trifecta/`

Additionally, we need to support:
- Portable mode (data alongside executable)
- Custom override via environment variable

## Decision

We will use a native-first approach with the following hierarchy:

### Path Resolution Priority

1. **`TRIFECTA_HOME` env var** (if set) - highest priority
2. **Platform-native directory** - per OS conventions
3. **Portable fallback** - `./.trifecta/` in repo root (last resort)

### Platform-Specific Paths

```python
def get_platform_data_dir() -> Path:
    """Get platform-appropriate data directory."""
    if trifecta_home := os.environ.get("TRIFECTA_HOME"):
        return Path(trifecta_home)

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "trifecta"
    elif sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "trifecta"
    else:  # linux, freebsd, etc.
        return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "trifecta"
```

### Segment-Specific Subdirectories

All paths derived from `SegmentRef`:

```
{platform_data_dir}/
├── repos/                     # SQLite databases
│   └── {repo_id}.db
├── daemon/                   # Daemon socket + PID
├── cache/                    # Cached data
│   └── {segment_id}/
├── config/                   # Configuration
│   └── {segment_id}.json
└── telemetry/                # Event logs
    └── {segment_id}/
```

## Consequences

### Positive
- Follows platform conventions (macOS Guidelines, XDG on Linux)
- User expects data in familiar locations
- Easy to find for debugging
- Portable mode for CI/embedded use

### Negative
- Must handle path separator differences
- Migration needed if changing default locations
- Environment variable may be overlooked

## Implementation Notes

- Use `platformdirs` library for cross-platform paths
- Document environment variables clearly
- Add migration utility for path changes

## Related

- WO-0041: SSOT + Contratos + Skeleton
- WO-0042: CLI Adelgazado + Repo Commands
- WO-0043: SQLite + Daemon + Operación Real
