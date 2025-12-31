# T9.3.2 Plan Evaluation Dataset v2 - NL (Natural Language Only)

**Purpose**: Natural language generalization testing for ctx.plan with expected labels for accuracy scoring
**Date**: 2025-12-31
**Total Tasks**: 40 (20 new + 10 ambiguous + 10 edge)
**Mode**: NL-only - NO "feature:" prefix allowed

---

## New Tasks (20)

Same domain as v1 (AST/Trifecta/PCC/context pack/telemetry/cli) with different phrasing.

<!-- Task IDs: T9V2NL-001 to T9V2NL-020 -->
<!-- Format: task_id | task_string | expected_feature_id | notes -->

1. "can you show me the token counting logic" | token_estimation | L2 match via "token counting"
2. "where would i find stats about search performance" | observability_telemetry | L2 match via "search performance"
3. "explain how primes organize the reading list" | prime_indexing | L2 match via "prime reading list"
4. "i need to design a ctx export feature" | fallback | No trigger match
5. "walk through the chunk retrieval flow" | chunk_retrieval_flow | L2 match via "chunk retrieval"
6. "what does the clean architecture look like here" | arch_overview | L2 match via "clean architecture"
7. "describe how telemetry events get recorded" | observability_telemetry | L2 match via "event tracking"
8. "help me create a ctx trends command" | fallback | No trigger match
9. "is the context pack validation passing" | context_pack | L2 match via "validate context"
10. "what is the prime file format" | prime_indexing | L2 match via "prime file format"
11. "show how to implement a summary use case" | code_navigation | L2 match via "implement use case"
12. "locate the GetChunkUseCase implementation" | get_chunk_use_case | L2 match via "locate GetChunkUseCase"
13. "where is the event flush mechanism defined" | telemetry_flush | L2 match via "event flush"
14. "list all typer commands available" | cli_commands | L2 match via "list commands"
15. "what files exist under src/domain" | directory_listing | L2 match via "files under src"
16. "show me the token estimation formula" | token_estimation | L2 match via "token formula"
17. "how is the Telemetry class constructed" | symbol_surface | Symbol query
18. "what imports are needed for the report generator" | import_statements | L2 match via "imports needed"
19. "find where budgets get calculated for searches" | observability_telemetry | Related to telemetry
20. "design a ctx validate workflow" | context_pack | Related to validation

---

## Ambiguous Tasks (10)

Tasks with unclear intent, poor phrasing, or multiple interpretations.

<!-- Task IDs: T9V2NL-021 to T9V2NL-030 -->

21. "the thing for loading context" | fallback | No trigger match
22. "stats stuff" | observability_telemetry | L3 match via "stats" term
23. "how does it work" | fallback | No trigger match
24. "build command not working" | context_pack | L3 match via "build" term
25. "telemetry" | observability_telemetry | L2 match via "telemetry" (single-word)
26. "where to find code" | fallback | No clear match
27. "architecture" | fallback | Should be ambiguous (guardrail prevents single-word priority 2)
28. "the prime thing" | prime_indexing | L3 match via "prime" term
29. "implement something" | fallback | "something" is unspecified
30. "search files" | fallback | No clear match

---

## Edge Cases (10)

Tasks mixing multiple concepts or boundary conditions.

<!-- Task IDs: T9V2NL-031 to T9V2NL-040 -->

31. "telemetry architecture overview" | fallback | Ambiguous - two single-word triggers conflict
32. "context pack validation status and budget estimation" | context_pack | L2 match via "validate context"
33. "cli command for searching with token limits" | cli_commands | L2 match via "ctx search"
34. "plan the implementation of a stats aggregation feature" | code_navigation | L2 match via "implement use case"
35. "symbols in the telemetry module and their relationships" | symbol_surface | Symbol-specific query
36. "how does search interact with the context pack build process" | context_pack | L2 match via "context pack build"
37. "design a new ctx benchmark command that measures latency" | observability_telemetry | Related to telemetry
38. "explain the event flow from cli to telemetry to reports" | observability_telemetry | Related to telemetry
39. "where do i start reading about clean architecture and primes" | arch_overview | L2 match via "clean architecture"
40. "implement a function that estimates tokens and flushes events" | token_estimation | L2 match via "token counting"

---

## Expected Distribution (T9.3.2)

| expected_feature_id | Count | Percentage |
|---------------------|-------|------------|
| observability_telemetry | 7 | 17.5% |
| context_pack | 4 | 10.0% |
| cli_commands | 2 | 5.0% |
| search | 0 | 0% |
| stats | 0 | 0% |
| arch_overview | 2 | 5.0% |
| symbol_surface | 2 | 5.0% |
| code_navigation | 2 | 5.0% |
| token_estimation | 3 | 7.5% |
| prime_indexing | 3 | 7.5% |
| chunk_retrieval_flow | 1 | 2.5% |
| get_chunk_use_case | 1 | 2.5% |
| telemetry_flush | 1 | 2.5% |
| import_statements | 1 | 2.5% |
| directory_listing | 1 | 2.5% |
| fallback | 10 | 25.0% |
| **TOTAL** | **40** | **100.0%** |

---

## Dataset Identity (Anti-Gaming)

- **Type**: NL-only (no feature: prefix)
- **Total tasks**: 40
- **Stable IDs**: T9V2NL-001 to T9V2NL-040
- **No mixing**: L1 explicit feature queries are in separate dataset (t9_plan_eval_tasks_v2_l1.md)

---

## Diff Note: How v1 phrases were avoided

1. **Verb variation**: v1 uses "explain", v2 uses "describe", "walk through", "show me"
2. **Structure variation**: v1 uses "where are...", v2 uses "where would i find...", "locate"
3. **Concept ordering**: v1 "context pack build process", v2 "chunk retrieval flow"
4. **Compound phrasing**: v1 "what is the architecture of", v2 "what does the clean architecture look like"
5. **Domain mixing**: Added edge cases that combine 2-3 concepts deliberately

**Deterministic guarantee**: Each v2 task was created by:
- Taking a v1 domain concept
- Applying a syntactic transformation (passive voice, question pattern shift, etc.)
- Or combining two concepts for edge cases

No v1 task string was copied as-is or with minor edits.
