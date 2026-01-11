: Telemetry.flush]
                          │ • BuildContextPack  │
                          │ • SearchUseCase     │          Locks/Ownership:
                          │ • GetChunkUseCase   │          ──────────────────
                          │ • SyncContext       │          • events.jsonl:  fcntl.LOCK_EX (telemetry.py:191)
                          │ • MacroLoad         │                           [SKIP write if busy]
                          │ • SessionAppend     │          • context_pack.json: NO LOCK (¡RIESGO!)
                          └────────┬────────────┘          • session_*.md:   AtomicWriter (NO LOCK)
                                   │                       • metrics.json:    Single writer (flush)
                                   v
                    ┌──────────────────────────┐
                    │  Infrastructure Layer    │
                    │  (infrastructure/)       │
                    ├──────────────────────────┤
                    │ • FileSystemAdapter      │  ─────> Disk I/O (read/write/scan)
                    │ • Telemetry              │  ─────> _ctx/telemetry/* (flock)
                    │ • TemplateRenderer       │  ─────> Generación MD templates
                    │ • ContextService         │  ─────> JSON load context_pack
                    │ • AliasLoader             │  ─────> YAML parse aliases
                    │ • PCCMetrics
