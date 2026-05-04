# Engram Discovery Contract

## Purpose
Define the multi-layered strategy for detecting the presence of Engram on a host machine without creating a hard dependency.

## Detection Layers (Priority Order)

| Layer | Method | Confidence |
|-------|--------|------------|
| 1. Explicit | `--engram-path` CLI flag | Highest |
| 2. Environment | `ENGRAM_HOME` environment variable | High |
| 3. Runtime | `command -v engram` (executable in PATH) | Medium |
| 4. Filesystem | Standard location check (`~/.engram`) | Medium |
| 5. Configuration | Existing MCP entries in agents containing "engram" | Low |

## Response Schema

A discovery attempt MUST return a structured result:

```json
{
  "detected": true,
  "configured": true,
  "reachable": true,
  "method": "env_var",
  "path": "/users/dev/.engram",
  "version": "1.2.0"
}
```

## Integration Strategy
- **Agnostic Principle**: If no layers return a positive result, Trifecta bootstrap SHALL proceed normally without mentioning Engram.
- **Strategic Coupling**: If detected, Trifecta bootstrap SHALL offer to link the two systems (e.g., adding "Trifecta + Engram" metadata to agent configs).
