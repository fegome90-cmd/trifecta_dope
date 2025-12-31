## Metrics for Success

1. **Tokens per Turn**: Target 40-60% reduction.
2. **Citation Rate**: Target >80% (using `[chunk_id]`).
3. **Search Recall**: Target >90%.
4. **Latency**: Enforce max 1 search + 1 get per turn.

---

```python
class ContextRouter:
    def route(self, task: str, segment: str) -> list[str]:
        """Route task to relevant chunks."""
        
        # Check if context_pack exists
        pack_path = Path(f"{segment}/_ctx/context_pack.json")
        
        if not pack_path.exists():
            # FALLBACK: Load complete files
            return self.load_complete_files(task, segment)
        
        # Use context pack with heuristic boost
        query = self.build_query(task)
        boosts = self.heuristic_boosts(task)
        
        results = ctx_search(
            segment=segment,
            query=query,
            k=5,
            filters={"boost": boosts}
        )
        
        return [hit["id"] for hit in results["hits"]]
```

---
