### Fixed False Negatives (2 tasks)

| Task ID | Task | Expected | Before (T9.3.3) | After (T9.3.4) | Why Fixed |
|---------|------|----------|-----------------|----------------|-----------|
| #20 | "design a ctx validate workflow" | context_pack | observability_telemetry (FN) | context_pack ✅ | L2 "ctx validate" exact match |
| #24 | "build command not working" | context_pack | cli_commands (FN) | context_pack ✅ | L2 "build command" exact match |
