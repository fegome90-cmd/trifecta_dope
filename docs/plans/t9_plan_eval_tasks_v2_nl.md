# T9.3.1 Plan Evaluation Dataset v2 - NL (Natural Language Only)

**Purpose**: Natural language generalization testing for ctx.plan
**Date**: 2025-12-31
**Total Tasks**: 40 (20 new + 10 ambiguous + 10 edge)
**Mode**: NL-only - NO "feature:" prefix allowed

---

## New Tasks (20)

Same domain as v1 (AST/Trifecta/PCC/context pack/telemetry/cli) with different phrasing.

<!-- Task IDs: T9V2NL-001 to T9V2NL-020 -->

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

<!-- Task IDs: T9V2NL-021 to T9V2NL-030 -->

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

<!-- Task IDs: T9V2NL-031 to T9V2NL-040 -->

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
