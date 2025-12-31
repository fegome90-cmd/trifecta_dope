### The Remaining Issues

1. **fallback_rate = 20.0% exactly at threshold**
   - 8 tasks fall back to L4
   - Threshold is < 20%, so exactly 20% fails
   - To pass, need <= 7 fallbacks (17.5%)

2. **8 Fallback Tasks**:
   1. "list all typer commands available" - should match cli_commands (nl_trigger: "list commands")
   2. "the thing for loading context" - truly ambiguous (expected fallback)
   3. "how does it work" - truly ambiguous (expected fallback)
   4. "telemetry" - single word, should match via unigram
   5. "where to find code" - vague (expected fallback)
   6. "architecture" - single word, should match via unigram
   7. "implement something" - "something" is unspecified (expected fallback)
   8. "telemetry architecture overview" - multi-concept (expected fallback)

3. **Investigation Needed**:
   - Tasks #1, #4, #6 should match via nl_triggers but aren't
   - Possible issues:
     - Unigram vs bigram matching
     - Normalization edge cases
     - Priority tie-breaking
