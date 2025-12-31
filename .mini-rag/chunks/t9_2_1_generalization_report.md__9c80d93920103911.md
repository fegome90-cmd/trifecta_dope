## Recommendations

To achieve <20% plan_miss_rate on holdout data:

1. **Add Synonym Triggers**
   - "token counting" → observability_telemetry
   - "chunk retrieval" → search
   - "typer commands" → cli_commands
   - "formula/equation" → function implementation

2. **Normalize Verb Patterns**
   - Add triggers for: "show me", "walk through", "locate", "list"
   - Combine with domain terms

3. **Increase Fuzzy Matching**
   - Consider word stem matching (count/counting/counted)
   - Consider semantic clustering (formula/function/implementation)

4. **Add "Unknown" Feature**
   - Catch-all for domain-ambiguous queries
   - Routes to prime entrypoints with explanation

5. **Per-Segment Tuning**
   - Each segment needs domain-specific triggers
   - Cross-segment generalization is not expected in PCC model

---
