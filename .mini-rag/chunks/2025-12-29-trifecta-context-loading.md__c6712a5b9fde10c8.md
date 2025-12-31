## Router Heurístico (Mínimo)

**Boosts basados en keywords**:

```python
def heuristic_boosts(query: str) -> dict:
    """Simple keyword-based boosts."""
    boosts = {}
    query_lower = query.lower()
    
    # Boost skill.md
    if any(kw in query_lower for kw in ["cómo usar", "comandos", "setup", "reglas"]):
        boosts["skill.md"] = 2.0
    
    # Boost prime.md
    if any(kw in query_lower for kw in ["diseño", "plan", "arquitectura", "docs"]):
        boosts["prime.md"] = 2.0
    
    # Boost session.md
    if any(kw in query_lower for kw in ["pasos", "checklist", "runbook", "handoff"]):
        boosts["session.md"] = 2.0
    
    # Boost agent.md
    if any(kw in query_lower for kw in ["stack", "tech", "implementación", "código"]):
        boosts["agent.md"] = 2.0
    
    return boosts
```

**Filtrado por presupuesto**:

```python
def filter_by_budget(hits: list, budget: int) -> list:
    """Filter hits to fit within token budget."""
    selected = []
    total_tokens = 0
    
    for hit in sorted(hits, key=lambda h: h["score"], reverse=True):
        if total_tokens + hit["token_est"] <= budget:
            selected.append(hit)
            total_tokens += hit["token_est"]
    
    return selected
```

---
