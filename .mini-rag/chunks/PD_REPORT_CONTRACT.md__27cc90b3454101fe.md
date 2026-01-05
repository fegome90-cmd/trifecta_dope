### Semantic Definitions

**`strong_hit`**: Observable behavior
- Query token appears in chunk title or ID with word-boundary matching
- AND chunk kind (from ID prefix) is `prime:`
- Purpose: Identifies high-signal chunks

**`support`**: Observable behavior
- Chunk text contains strict patterns matching code definitions
- Patterns include: `def <query>(`, `class <query>:`, `class <query>(`
- Guards: Filters out keywords, comments, and partial matches
- Purpose: Confirms query represents an actual code symbol
