### Denylist (Hard - Skip Parsing)
```python
HARD_DENYLIST = {
    ".git", ".env", ".env.local",
    "node_modules", "__pycache__", ".venv", "venv",
    "*.pyc", "*.pyo", "*.so", "*.egg-info"
}

def is_scannable(path: Path) -> bool:
    for part in path.parts:
        if part in HARD_DENYLIST:
            return False
    return True
```
