### 2. Presupuesto Duro + Máximo de Rondas

```python
class ContextBudget:
    def __init__(self):
        self.max_ctx_rounds = 2  # Máximo 2 búsquedas por turno
        self.max_tokens_per_round = 1200
        self.current_round = 0
        self.total_tokens = 0
    
    def can_request(self, token_est: int) -> bool:
        """Check if request fits budget."""
        if self.current_round >= self.max_ctx_rounds:
            return False
        if self.total_tokens + token_est > self.max_tokens_per_round:
            return False
        return True
    
    def record(self, token_est: int):
        """Record token usage."""
        self.total_tokens += token_est
        self.current_round += 1
```

**Fallback cuando se excede presupuesto**:
```python
if not budget.can_request(token_est):
    return {
        "error": "BUDGET_EXCEEDED",
        "message": "Insufficient context budget. Please refine your query or request specific chunks.",
        "available_tokens": budget.max_tokens_per_round - budget.total_tokens
    }
```

---
