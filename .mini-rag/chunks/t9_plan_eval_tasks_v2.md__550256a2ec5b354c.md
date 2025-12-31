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
