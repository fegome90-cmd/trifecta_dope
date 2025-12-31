## Remaining Misses (3/20)

| # | Task | Reason | Potential Fix |
|---|------|--------|---------------|
| 1 | "what is the architecture of the telemetry system?" | "architecture" matches arch_overview, but "telemetry system" matches observability_telemetry - conflict | Add combined trigger: "telemetry system architecture" |
| 2 | "import statements in telemetry_reports.py" | Too specific - needs AST-level symbol resolution | Covered by symbols_stub.md (v2 will have AST) |
| 3 | "method flush() implementation details" | Specific method name not in triggers | Add "flush implementation" trigger to observability_telemetry |

---
