## 3. Context Use Examples: Teaching Correct Usage

Just as Tool Use Examples teach correct patterns, we include **Context Use Examples** to teach when to seek evidence vs. when to proceed.

**Example A: Search for operational rules**
```
User: "What's the lock policy?"
Agent:
1. ctx.search(query="lock stale split-brain", k=5)
2. ctx.get(ids=[top 2], mode="excerpt", budget=800)
3. Respond citing [chunk_id]
```

**Example B: If evidence is missing, do not invent**
```
User: "Where does it say X is mandatory?"
Agent:
1. ctx.search(query="X mandatory MUST mandatory", k=8)
2. If no clear hits: respond "It does not appear in the indexed context" and suggest where to check.
```

---
