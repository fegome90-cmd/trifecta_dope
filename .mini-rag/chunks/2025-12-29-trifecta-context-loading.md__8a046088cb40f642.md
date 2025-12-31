## CLI Interface (Using Existing Trifecta)

```bash
# Load context for a task
trifecta load --segment debug_terminal --task "implement DT2-S1"

# Output: Markdown with skill.md + agent.md content
# Agent receives complete files, not chunks
```

**Integration with any agent:**
```python
# Works with Claude, Gemini, GPT, etc.
from trifecta import load_context

context = load_context(
    segment="debug_terminal",
    task="implement DT2-S1 sanitization"
)

# context = markdown string with complete files
# Inject into system prompt
agent.run(system_prompt=f"Task: ...\n\nContext:\n{context}")
```

---
