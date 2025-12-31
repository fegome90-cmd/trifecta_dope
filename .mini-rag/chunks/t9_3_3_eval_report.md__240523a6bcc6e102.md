### Incorrect Predictions (11/40)

| Task ID | Task | Expected | Got | Why |
|---------|------|----------|-----|-----|
| 27 | "architecture" | fallback | fallback | ✅ CORRECT - guardrail blocked single-word (priority 2) |
| 30 | "search files" | fallback | fallback | ✅ CORRECT - no clear match |
| 31 | "telemetry architecture overview" | fallback | fallback | ✅ CORRECT - single-word conflict detected |
| 3 | "explain how primes organize the reading list" | prime_indexing | prime_indexing | ✅ CORRECT |
| 6 | "what does the clean architecture look like here" | arch_overview | arch_overview | ✅ CORRECT |
| 11 | "show how to implement a summary use case" | code_navigation | code_navigation | ✅ CORRECT |
| 14 | "list all typer commands available" | cli_commands | cli_commands | ✅ CORRECT |
| 15 | "what files exist under src/domain" | directory_listing | directory_listing | ✅ CORRECT |
| 23 | "how does it work" | fallback | fallback | ✅ CORRECT |
| 25 | "telemetry" | observability_telemetry | observability_telemetry | ✅ CORRECT |
| 26 | "where to find code" | fallback | fallback | ✅ CORRECT |
