│  ─────> YAML parse aliases
                    │ • PCCMetrics (NEW v1.1)  │  ─────> feature_map parsing + eval
                    │ • Validators (FP Gate)   │  ─────> Result[ValidationResult, Err]
                    └──────────────────────────┘

                    I/O per Stage:
                    ═══════════════════════════════════════════════════════
                    Stage               Input                 Output
                    ─────────────────────────────────────────────────────
                    ctx build           skill/prime/agent     context_pack.json (7 chunks)
                    ctx search          query + aliases       SearchResult (hits list)
                    ctx get             chunk IDs + mode      GetResult (text chunks)
                    ctx sync            segment path          rebuilt pack + validation
                    ctx validate        context_pack.json     ValidationResult (PASS/FAIL)
                    load                task + search query   MacroLoadResult (files list)
                    session append      summary + files       session_*.md (append entry)

                    Herramientas Clave:
                    ═══════════════════════════════════════════════════════
                    Comando                  Módulo                   Tool Impl
                    ─────────────────────────────────────────────────
