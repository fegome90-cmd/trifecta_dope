## Parser Example

```python
# Parse PD_REPORT (order-independent)
for line in output.split("\n"):
    if line.startswith("PD_REPORT v="):
        metrics = {}
        for match in re.finditer(r"(\w+)=(\w+)", line):
            metrics[match.group(1)] = match.group(2)

        # Extract known keys (ignore unknown)
        version = int(metrics.get("v", 0))
        stop_reason = metrics.get("stop_reason")
        chunks_returned = int(metrics.get("chunks_returned", 0))
        # ... etc
```
