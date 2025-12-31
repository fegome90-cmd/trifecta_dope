### Interpretation

The high alias rate (82.5%) indicates:
- Strong generalization: most natural language queries match via structured triggers
- Low fallback rate (17.5%): only truly ambiguous queries fall back
- Zero true_zero_guidance: all tasks return some guidance

The 7 remaining fallbacks are all truly ambiguous queries:
1. "the thing for loading context" - no specific keywords
2. "how does it work" - no domain context
3. "telemetry" - single keyword, no intent
4. "where to find code" - too vague
5. "architecture" - single keyword
6. "implement something" - "something" is unspecified
7. "telemetry architecture overview" - multi-concept edge case
