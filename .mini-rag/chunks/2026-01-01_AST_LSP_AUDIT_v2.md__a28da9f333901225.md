### 2. ❌ "Expecting LSP to be always warm"
**Why bad here:** Cold start 2–5s blocks user queries.  
**Lean alternative:** Instant fallback to Tree-sitter (<50ms), spawn LSP async for next query.
