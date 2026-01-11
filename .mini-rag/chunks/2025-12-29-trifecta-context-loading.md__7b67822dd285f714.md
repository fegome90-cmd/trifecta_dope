## Heuristic Selection Rules

```python
def select_files(task: str, segment: str) -> list[str]:
    """
    Select relevant Trifecta files based on task keywords.
    No LLM needed - simple heuristics.
    """
    files = []
    task_lower = task.lower()

    # ALWAYS include skill.md (core rules)
    files.append(f"{segment}/skill.md")

    # Implementation/debugging → agent.md
    if any(kw in task_lower for kw in ["implement", "debug", "fix", "build"]):
        files.append(f"{segment}/agent.md")

    # Planning/design → prime.md
    if any(kw in task_lower for kw in ["plan", "design", "architecture"]):
        files.append(f"{segment}/prime.md")

    # Session review/handoff → session.md
    if any(kw in task_lower for kw in ["session", "handoff", "history", "previous"]):
        files.append(f"{segment}/session.md")

    # Always include README for quick reference
    files.append(f"{segment}/README_TF.md")

    return files
```

**No chunking. No RAG. No LLM orchestrator.**

---
