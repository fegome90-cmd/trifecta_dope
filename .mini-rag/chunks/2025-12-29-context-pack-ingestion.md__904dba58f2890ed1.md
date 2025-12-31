### 2. Digest Determinista (Scoring)

**Problem**: "First 800 chars" is not semantic quality.

**Solution**: Score-based selection of top-2 chunks per doc:

```python
def score_chunk(title: str, level: int, text: str) -> int:
    score = 0
    title_lower = title.lower()

    # Keywords that indicate relevance
    if any(kw in title_lower for kw in ["core", "rules", "workflow", "commands",
                                            "usage", "setup", "api", "architecture"]):
        score += 3

    # Higher headings are more important
    if level <= 2:
        score += 2

    # Penalize empty overview/intro
    if kw in ["overview", "intro"] and len(text) < 300:
        score -= 2

    return score

# Take top-2 chunks by score per doc, max 1200 chars total
```
