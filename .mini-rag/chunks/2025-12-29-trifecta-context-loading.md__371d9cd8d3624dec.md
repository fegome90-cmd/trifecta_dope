### 2. File Selector

**File**: `trifecta_dope/src/application/context_loader.py` (NEW)

```python
from pathlib import Path

def select_files(task: str, segment: str) -> list[Path]:
    """Select files based on task keywords."""
    base = Path(f"/projects/{segment}")
    files = []
    task_lower = task.lower()
    
    # Always skill.md
    files.append(base / "skill.md")
    
    # Conditional files
    if any(kw in task_lower for kw in ["implement", "debug", "fix"]):
        files.append(base / "_ctx/agent.md")
    
    if any(kw in task_lower for kw in ["plan", "design"]):
        files.append(base / "_ctx/prime.md")
    
    if any(kw in task_lower for kw in ["session", "handoff"]):
        files.append(base / "_ctx/session.md")
    
    files.append(base / "README_TF.md")
    
    return [f for f in files if f.exists()]

def format_context(files: list[Path]) -> str:
    """Format files as markdown."""
    sections = []
    
    for file in files:
        content = file.read_text()
        sections.append(f"## {file.name}\n\n{content}")
    
    return "\n\n---\n\n".join(sections)
```

---
