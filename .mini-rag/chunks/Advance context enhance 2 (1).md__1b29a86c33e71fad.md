### Solution: Add 3–5 usage examples

These aren’t “nice prompts”—they’re behavior control.

**Example A: Search for operational rules**

```
User: "What's the lock policy?"

Agent approach:
1. ctx.search(query="lock stale split-brain", k=5)
2. ctx.get(ids=[top 2], mode="excerpt", budget=800)
3. Respond citing [chunk_id]
```

**Example B: Handle missing evidence**

```
User: "Where does it say X is mandatory?"

Agent approach:
1. ctx.search(query="X mandatory MUST", k=8)
2. If no clear hits: respond "No evidence in indexed context"
   and suggest where to look
3. Do NOT invent requirements
```

This is analogous to Tool Use Examples: you teach “correct usage,” not just valid JSON.
