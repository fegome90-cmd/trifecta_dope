### Deliverables Completed

| Deliverable | Status | Evidence |
|-------------|--------|----------|
| A) 3-level matching | ✅ | `src/application/plan_use_case.py` |
| L1: Explicit feature id | ✅ | `_match_l1_explicit_feature()` |
| L2: Alias match | ✅ | `_match_l2_alias()` with structured triggers |
| L3: Fallback entrypoints | ✅ | `_parse_prime_entrypoints()` |
| B) Feature_map refactor | ✅ | `_ctx/aliases.yaml` (schema v2) |
| C1) arch_overview feature | ✅ | `arch_overview` in aliases.yaml |
| C2) symbol_surface feature | ✅ | `symbol_surface` in aliases.yaml |
| C3) code_navigation feature | ✅ | `code_navigation` in aliases.yaml |
| C4) Stub artifacts | ✅ | `_ctx/generated/repo_map.md`, `symbols_stub.md` |
| D) Telemetry for ctx.plan | ✅ | `selected_by`, `match_terms_count`, `returned_chunks_count`, `returned_paths_count` |
| E) eval-plan command | ✅ | `ctx eval-plan` in CLI |
