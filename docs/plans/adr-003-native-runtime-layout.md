# ADR: Native-First Runtime Layout

## Status
Accepted

## Context
Trifecta should store runtime data in standard Mac/Linux locations (~/.config, ~/.local/share, ~/.cache) instead of inside repositories.

## Decision
Standard runtime layout:
```
~/.config/trifecta/          # Global config
~/.local/share/trifecta/     # Global state (repos metadata)
~/.cache/trifecta/           # Cache

~/.local/share/trifecta/repos/<repo_id>/
  repo.json                  # metadata
  ast.db                    # AST cache
  anchors.db                # anchors/symbols
  search.db                 # search index
  runtime.db                # runtime metadata
  daemon/
    socket
    pid
    log
  locks/
  telemetry/
  cache/
```

## Consequences
- No data stored inside repositories
- Easy cleanup by removing directory
- Portable across machines (just copy the dirs)
