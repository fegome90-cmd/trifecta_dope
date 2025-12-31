### 1. Fence-Aware Chunking

**Problem**: Headings inside code blocks (``` fence) should not create chunks.

**Solution**: State machine tracking `in_fence`:

```python
in_fence = False
for line in lines:
    if line.strip().startswith(("```", "~~~")):
        in_fence = not in_fence
    elif HEADING_RE.match(line) and not in_fence:
        # New chunk
```
