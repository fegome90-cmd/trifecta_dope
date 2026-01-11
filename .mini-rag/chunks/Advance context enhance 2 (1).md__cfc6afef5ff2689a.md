### Example: Evidence gathering with budget

```python
def gather_evidence(segment: str, query: str, budget: int = 1200) -> str:
    """
    Orchestrate search + retrieval within token budget.
    """
    hits = ctx_search(segment=segment, query=query, k=8)

    # Sort by value per token
    hits = sorted(
        hits,
        key=lambda h: h["score"] / max(h["token_est"], 1),
        reverse=True
    )

    # Select chunks that fit budget
    chosen = []
    used = 0
    for h in hits:
        if used + h["token_est"] > budget:
            continue
        chosen.append(h["id"])
        used += h["token_est"]
        if len(chosen) >= 4:  # max 4 chunks per query
            break

    # Retrieve with citation-ready format
    chunks = ctx_get(
        segment=segment,
        ids=chosen,
        mode="excerpt",
        budget_token_est=budget
    )

    # Format for model consumption
    lines = ["EVIDENCE (read-only):"]
    for c in chunks:
        path = " > ".join(c["title_path"])
        lines.append(f"\n[{c['id']}] {path}\n{c['text'].strip()}")

    return "\n".join(lines)
```

**Hypothesis**: If you keep prompts short and bring localized evidence, you reduce “lost in the middle” and noise. This aligns with empirical findings about degradation in long contexts.
