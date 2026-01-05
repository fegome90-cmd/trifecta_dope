### Per-Task Transitions (Changed Tasks Only)

| Task ID | Task | Expected | Baseline (T9.3.4) | Current (T9.3.5) | Transition | Was FP Before? | False Fallback Now? |
|--------:|------|----------|------------------|------------------|------------|----------------|---------------------|
| 17 | how is the Telemetry class constructed | symbol_surface | observability_telemetry | symbol_surface | nl_trigger->nl_trigger | yes | no |
| 20 | design a ctx validate workflow | context_pack | observability_telemetry | context_pack | alias->nl_trigger | yes | no |
| 24 | build command not working | context_pack | cli_commands | context_pack | alias->nl_trigger | yes | no |
| 25 | telemetry | observability_telemetry | observability_telemetry | fallback | nl_trigger->fallback | no | yes |
| 35 | symbols in the telemetry module and their relationships | symbol_surface | observability_telemetry | fallback | nl_trigger->fallback | yes | yes |
