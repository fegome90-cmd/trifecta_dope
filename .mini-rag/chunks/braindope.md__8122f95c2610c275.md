## Hook Logic (Claude Code)
```python
import re
from pathlib import Path

def expand_resource_refs(skill_content: str, segment_path: Path) -> str:
    """Expande referencias @_ctx/... on-demand."""
    resource_refs = re.findall(r'@(_ctx/[^\s]+\.md)', skill_content)
    
    for ref in resource_refs:
        resource_path = segment_path / ref
        if resource_path.exists():
            resource_content = resource_path.read_text()
            skill_content = skill_content.replace(
                f'@{ref}',
                f'\n<!-- EXPANDED: {ref} -->\n{resource_content}\n<!-- END -->\n'
            )
    return skill_content
```
