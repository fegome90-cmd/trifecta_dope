```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRIFECTA PIPELINE (MVP Operacional)                                    │
└─────────────────────────────────────────────────────────────────────────┘

ENTRADAS                    PROCESOS                    ARTEFACTOS EN DISCO
═══════════════════════════════════════════════════════════════════════════

CLI Args                    ┌─────────────────┐          _ctx/
  --segment PATH     ───────>│  CLI Router     │            ├── context_pack.json  [RW: BuildUseCase]
  --query "term"             │  (cli.py)       │            ├── session_*.md        [APPEND: session cmd]
  --task "desc"              └────────┬────────┘            ├── prime_*.md          [R: BuildUseCase]
                                      │                     ├── agent.md            [R: LoadUseCase]
                                      v                     ├── aliases.yaml        [R: SearchUseCase]
                          ┌─────────────────────┐          └── telemetry/
                          │  Use Cases Layer    │                ├── events.jsonl  [APPEND: Telemetry]
                          │  (application/)     │                ├── metrics.json  [RW: Telemetry.flush]
                          ├─────────────────────┤                └── last_run.json [W: Telemetry.flush]
                          │ • BuildContextPack  │
