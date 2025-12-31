### 1. Extend Trifecta CLI

**File**: `trifecta_dope/src/infrastructure/cli.py`

Add `load` command:
```python
@app.command()
def load(
    segment: str,
    task: str,
    output: Optional[str] = None
):
    """Load context files for a task."""
    files = select_files(task, segment)
    context = format_context(files)
    
    if output:
        Path(output).write_text(context)
    else:
        print(context)
```
