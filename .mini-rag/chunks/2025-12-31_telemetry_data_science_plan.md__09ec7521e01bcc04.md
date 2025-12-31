```
┌─────────────────────────────────────────────────────────────┐
│                    Trifecta CLI (User/Agent)                 │
│                                                              │
│  ctx.search → Telemetry.event() → events.jsonl (append)    │
│  ctx.get    → Telemetry.event() → metrics.json (aggregate) │
│  ctx.sync   → Telemetry.event() → last_run.json (summary)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    New: CLI Report Command                   │
│                                                              │
│  $ trifecta telemetry report [--last N] [--format table]    │
│  $ trifecta telemetry export [--format json|csv]            │
│  $ trifecta telemetry chart [--type hits|latency]           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   New: Agent Skill (telemetry-analyze)       │
│                                                              │
│  Usa la skill → Output conciso en Markdown                   │
│  - Tablas ASCII                                              │
│  - Métricas clave solo
