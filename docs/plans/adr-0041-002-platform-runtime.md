# ADR-0041-002: Platform Runtime Architecture

**Date**: 2026-03-06
**Status**: Proposed
**Epic**: E-V1 (Trifecta V1 Global Platform)
**WO**: WO-0041

## Context

Trifecta needs a Platform Runtime to manage:
- Repository registry (SQLite-based per-repo storage)
- Daemon lifecycle (start/stop/status/restart)
- Health checks
- Recovery operations

Currently these responsibilities are scattered across different modules.

## Decision

We will create a Platform Runtime with the following components:

### Architecture

```
Platform Runtime
├── Registry (Protocol/Interface)
│   └── repo_store.py (implementation - WO-0043)
├── Daemon Manager (Protocol/Interface)  
│   └── daemon_manager.py (implementation - WO-0043)
├── Runtime Manager (Orchestrator)
│   └── runtime_manager.py (skeleton - WO-0041, impl - WO-0043)
└── Health Checker
    └── health.py (implementation - WO-0043)
```

### Design Principles

1. **Protocol-first**: Define interfaces/abstract classes, implement later
2. **Lazy initialization**: Don't start daemon until needed
3. **Idempotent operations**: Safe to call multiple times
4. **Native paths**: Use platform-specific directories via SegmentRef

### Directory Structure

```
~/.trifecta/
├── repos/
│   └── {repo_id}.db          # SQLite per-repo
├── daemon/
│   ├── socket                 # Unix socket
│   └── pid                    # PID file
├── cache/
│   └── {segment_id}/          # Segment-specific cache
└── config/
    └── {segment_id}.json      # Segment configuration
```

## Consequences

### Positive
- Clear separation of concerns
- Easy to test with mock implementations
- Platform-native directory handling
- Extensible for new features

### Negative
- Initial overhead for skeleton setup
- Must maintain interface compatibility

## Implementation Notes

- WO-0041: Create skeleton interfaces in `src/trifecta/platform/`
- WO-0043: Implement actual SQLite, daemon, and operations
- Use `SegmentRef` from ADR-0041-001 for all paths

## Related

- WO-0041: SSOT + Contratos + Skeleton
- WO-0042: CLI Adelgazado + Repo Commands
- WO-0043: SQLite + Daemon + Operación Real
