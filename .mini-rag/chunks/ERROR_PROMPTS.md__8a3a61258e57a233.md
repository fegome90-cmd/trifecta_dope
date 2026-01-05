### Programmatic Usage

```python
from scripts.harness_blackbox import run_command_with_extraction

result = run_command_with_extraction(
    ["uv", "run", "trifecta", "ctx", "get", "-s", ".", "--ids", "prime:abc", "--pd-report"]
)

if not result["success"]:
    if "error_prompt" in result:
        print(result["error_prompt"])  # Show recovery steps
```
