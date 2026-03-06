# ADR: Platform Runtime

## Status
Accepted

## Context
Trifecta V1 needs a platform layer for managing repositories, daemon lifecycle, and runtime state independently of the LSP subsystem.

## Decision
The platform layer (`src/platform/`) provides:
- Registry: Repository registration and lookup (SQLite-backed)
- DaemonManager: Process lifecycle management
- HealthChecker: Runtime health verification
- RuntimeManager: Directory and state management

## Consequences
- Clear separation between platform and LSP concerns
- Repository operations work without LSP daemon
- Daemon can be started on-demand per-repo
