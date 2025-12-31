### Why v1 Passed, v2 Failed

1. **Trigger Phrasing Mismatch**
   - v1: "function _estimate_tokens implementation"
   - v2: "show me the token estimation formula"
   - Trigger: "function implementation" (matches v1, not v2)

2. **Verb/Preposition Variance**
   - v1: "where are the CLI commands defined"
   - v2: "list all typer commands available"
   - Trigger: "cli commands defined" (matches v1, not v2)

3. **Synonym Gaps**
   - "counting" vs "tracking"
   - "retrieval flow" vs "search"
   - "formula" vs "function"

4. **Overfitting to Exact Phrases**
   - Triggers were tuned based on v1 task wording
   - Same semantic meaning, different syntax → miss

---
