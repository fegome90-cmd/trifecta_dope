#### 2. **Circuit Breaker** (para fuentes, no LLM)

**De**: orchestrator/circuit-breaker  
**Para Trifecta**: Fail closed en archivos problemáticos

```python
class SourceCircuitBreaker:
    def __init__(self, max_chars: int = 100_000):
        self.max_chars = max_chars

    def check_file(self, path: Path) -> bool:
        """Validate file before processing."""
        # Size check
        if path.stat().st_size > self.max_chars:
            logger.warning(f"File too large: {path}")
            return False

        # Encoding check
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            logger.error(f"Invalid encoding: {path}")
            return False

        # Fence balance check
        fence_count = content.count("```")
        if fence_count % 2 != 0:
            logger.warning(f"Unbalanced fences: {path}")

        return True
```

**ROI**: Medio-alto. Evita packs semi-rotos.

---
