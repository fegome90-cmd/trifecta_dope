### Sistema de Scoring

```python
def score_chunk(title: str, level: int, text: str) -> int:
    """
    Score a chunk for digest inclusion.
    Higher score = more relevant.
    """
    score = 0
    title_lower = title.lower()

    # +3 puntos: Keywords relevantes
    relevant_keywords = [
        "core", "rules", "workflow", "commands",
        "usage", "setup", "api", "architecture",
        "critical", "mandatory", "protocol"
    ]
    if any(kw in title_lower for kw in relevant_keywords):
        score += 3

    # +2 puntos: Headings de alto nivel (## o #)
    if level <= 2:
        score += 2

    # -2 puntos: Overview/Intro vacío (fluff)
    fluff_keywords = ["overview", "intro", "introduction"]
    if any(kw in title_lower for kw in fluff_keywords) and len(text) < 300:
        score -= 2

    return score
```
