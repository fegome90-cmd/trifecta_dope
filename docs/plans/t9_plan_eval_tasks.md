# T9 Plan Evaluation Dataset

**Purpose**: Evaluate ctx.plan effectiveness in reducing zero-hits
**Date**: 2025-12-31
**Total Tasks**: 20 (10 meta + 10 impl)

---

## Meta Tasks (10)

Tasks asking about architecture, design, planning, how-to:

1. "how does the context pack build process work?"
2. "what is the architecture of the telemetry system?"
3. "where are the CLI commands defined?"
4. "plan the implementation of token tracking"
5. "guide me through the search use case"
6. "overview of the clean architecture layers"
7. "explain the telemetry event flow"
8. "design a new ctx.stats command"
9. "status of the context pack validation"
10. "description of the prime structure"

---

## Impl Tasks (10)

Tasks asking about specific code, symbols, functions, files:

1. "implement the stats use case function"
2. "find the SearchUseCase class"
3. "code for telemetry.event() method"
4. "symbols in cli.py for ctx commands"
5. "files in src/application/ directory"
6. "function _estimate_tokens implementation"
7. "class Telemetry initialization"
8. "import statements in telemetry_reports.py"
9. "method flush() implementation details"
10. "code pattern for use case execute"

---

## Expected Results

### Baseline (ctx.search alone)

- Expected zero-hits: ~60-70%
- Based on current telemetry: 68.4% zero-hits

### Target (ctx.plan)

- Target zero-hits: <20%
- Goal: ctx.plan should route to relevant features even when search fails

### Success Criteria

| Metric | Target |
|--------|--------|
| plan_hit rate | >70% (14/20 tasks match a feature) |
| zero_hits with plan | <20% (4/20 tasks have no relevant chunks) |
| Combined improvement | >50% reduction in zero-hits |
