#### ctx search

```bash
$ uv run trifecta ctx search -s . -q "context" 2>&1
Search Results (3 hits):

1. [agent:abafe98332] agent_trifecta_dope.md
   Score: 0.50 | Tokens: ~1067
   Preview: ---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2026-01-01
default...

2. [session:1d37e51fdb] session_trifecta_dope.md
   Score: 0.50 | Tokens: ~3967
   Preview: # session.md - Trifecta Context Runbook

segment: trifecta-dope

## Purpose
This file is a **runbook** for using Trifect...

3. [ref:trifecta_dope/README.md:c2d9ad0077] README.md
   Score: 0.50 | Tokens: ~3347
   Preview: # Trifecta Generator

> **North Star**: Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 ar...
```
