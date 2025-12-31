# T9.3 Plan Evaluation Dataset v2 (Holdout + L1)

**Purpose**: Generalization testing for ctx.plan (anti-overfitting)
**Date**: 2025-12-31
**Total Tasks**: 48 (20 new + 10 ambiguous + 10 edge + 8 L1)

**T9.3 Update**: Added L1 explicit feature queries to test feature:<id> matching

---

## L1 Explicit Feature Queries (8)

Test explicit feature:<id> syntax for feature_hit_rate metric.

41. "feature:token_estimation show me the formula"
42. "feature:observability_telemetry stats"
43. "feature:get_chunk_use_case locate the class"
44. "feature:prime_indexing explain the reading list"
45. "feature:chunk_retrieval_flow how does it work"
46. "feature:cli_commands list all commands"
47. "feature:telemetry_flush explain flush"
48. "feature:directory_listing show me files under src"

---

## New Tasks (20)

Same domain as v1 (AST/Trifecta/PCC/context pack/telemetry/cli) with different phrasing.

<!-- Task IDs: T9V2-001 to T9V2-020 -->

1. "can you show me the token counting logic"
2. "where would i find stats about search performance"
3. "explain how primes organize the reading list"
4. "i need to design a ctx export feature"
5. "walk through the chunk retrieval flow"
6. "what does the clean architecture look like here"
7. "describe how telemetry events get recorded"
8. "help me create a ctx trends command"
9. "is the context pack validation passing"
10. "what is the prime file format"
11. "show how to implement a summary use case"
12. "locate the GetChunkUseCase implementation"
13. "where is the event flush mechanism defined"
14. "list all typer commands available"
15. "what files exist under src/domain"
16. "show me the token estimation formula"
17. "how is the Telemetry class constructed"
18. "what imports are needed for the report generator"
19. "find where budgets get calculated for searches"
20. "design a ctx validate workflow"

---

## Ambiguous Tasks (10)

Tasks with unclear intent, poor phrasing, or multiple interpretations.

<!-- Task IDs: T9V2-021 to T9V2-030 -->

21. "the thing for loading context"
22. "stats stuff"
23. "how does it work"
24. "build command not working"
25. "telemetry"
26. "where to find code"
27. "architecture"
28. "the prime thing"
29. "implement something"
30. "search files"

---

## Edge Cases (10)

Tasks mixing multiple concepts or boundary conditions.

<!-- Task IDs: T9V2-031 to T9V2-040 -->

31. "telemetry architecture overview"
32. "context pack validation status and budget estimation"
33. "cli command for searching with token limits"
34. "plan the implementation of a stats aggregation feature"
35. "symbols in the telemetry module and their relationships"
36. "how does search interact with the context pack build process"
37. "design a new ctx benchmark command that measures latency"
38. "explain the event flow from cli to telemetry to reports"
39. "where do i start reading about clean architecture and primes"
40. "implement a function that estimates tokens and flushes events"

---

## Audit Tags (Expected Buckets - Not Used by Router)

For audit purposes only - the router does NOT see these.

| Task ID | Expected Bucket | Notes |
|---------|----------------|-------|
| T9V2-001 | impl | Token counting logic |
| T9V2-002 | meta | Stats about search |
| T9V2-003 | meta | Prime organization |
| T9V2-004 | meta | Design a feature |
| T9V2-005 | meta | Walk through flow |
| T9V2-006 | meta | Architecture overview |
| T9V2-007 | meta | Event flow |
| T9V2-008 | meta | Design command |
| T9V2-009 | meta | Validation status |
| T9V2-010 | meta | Prime format |
| T9V2-011 | impl | Implement use case |
| T9V2-012 | impl | Find class |
| T9V2-013 | impl | Flush mechanism |
| T9V2-014 | meta | CLI commands |
| T9V2-015 | impl | Directory listing |
| T9V2-016 | impl | Formula |
| T9V2-017 | impl | Class constructor |
| T9V2-018 | impl | Import statements |
| T9V2-019 | impl | Budget calculation |
| T9V2-020 | unknown | Mixed concept |
| T9V2-021 | unknown | Too vague |
| T9V2-022 | unknown | Too vague |
| T9V2-023 | unknown | No context |
| T9V2-024 | unknown | Error report without detail |
| T9V2-025 | unknown | Single keyword |
| T9V2-026 | unknown | No specifics |
| T9V2-027 | unknown | Single keyword |
| T9V2-028 | unknown | Vague reference |
| T9V2-029 | unknown | No specifics |
| T9V2-030 | unknown | Too generic |
| T9V2-031 | meta | Architecture + telemetry mix |
| T9V2-032 | meta | Validation + budget mix |
| T9V2-033 | impl | CLI + search + tokens mix |
| T9V2-034 | meta | Plan + stats mix |
| T9V2-035 | impl | Symbols + telemetry mix |
| T9V2-036 | meta | Search + build interaction |
| T9V2-037 | meta | Design + benchmark + latency |
| T9V2-038 | meta | Multi-component flow |
| T9V2-039 | meta | Architecture + prime mix |
| T9V2-040 | impl | Multi-function task |

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
