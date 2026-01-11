### 2.2 Implementación

**Ubicación**: `src/application/context_service.py:265-301`

```python
def _skeletonize(self, text: str) -> str:
    """
    Extract headings and code block markers to create a structure view.
    """
    skeleton_lines = []
    in_code_block = False

    for line in text.splitlines():
        line_strip = line.strip()

        # Keep headings
        if line_strip.startswith("#"):
            skeleton_lines.append(line)
            continue

        # Keep code block markers
        if line_strip.startswith("```"):
            skeleton_lines.append(line)
            in_code_block = not in_code_block
            continue

        # If inside code block, keep first line (signature)
        if (
            in_code_block
            and len(skeleton_lines) > 0
            and skeleton_lines[-1].strip().startswith("```")
        ):
            if any(
                kw in line
                for kw in ["def ", "class ", "interface ", "function ", "const ", "var "]
            ):
                skeleton_lines.append(f"  {line_strip}")

    return "\n".join(skeleton_lines) if skeleton_lines else text[:200] + "..."
```
