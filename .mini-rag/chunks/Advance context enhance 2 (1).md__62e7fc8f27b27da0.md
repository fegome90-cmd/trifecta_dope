### Search doesn’t require embeddings

BM25 or full-text search is sufficient to start. Anthropic mentions regex and BM25 approaches for tool search—the same applies here. You can add hybrid search (BM25 + embeddings) later if metrics show recall problems, but don’t over-engineer upfront.

Example search interaction:

```python
# Agent requests
ctx_search(
    segment="myproject",
    query="lock policy stale timeout",
    k=5
)

# Returns
[
    {
        "id": "ops:a3f8b2",
        "doc": "operations.md",
        "title_path": ["Operations", "Lock Management", "Timeout Policy"],
        "preview": "Locks automatically expire after 30 seconds of inactivity...",
        "token_est": 150,
        "score": 0.92
    },
    # ... more results
]
```
