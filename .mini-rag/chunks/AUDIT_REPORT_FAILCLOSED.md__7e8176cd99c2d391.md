```python
import json
import random
from datetime import datetime, timedelta

def generate_event(event_type: str, ts: datetime) -> dict:
    """Generate synthetic telemetry event."""
    base = {
        "ts": ts.isoformat(),
        "run_id": f"run_{int(ts.timestamp())}",
        "segment_id": "abc12345",
        "cmd": event_type,
        "args": {},
        "result": {},
        "timing_ms": random.randint(1, 100),
        "warnings": [],
        "x": {}
    }

    if event_type == "session.entry":
        base["args"] = {
            "summary": f"Synthetic task {random.randint(1, 1000)}",
            "type": random.choice(["debug", "develop", "document", "refactor"]),
            "files": [f"src/file_{random.randint(1, 50)}.py"],
            "commands": ["pytest"]
        }
        base["result"] = {"outcome": random.choice(["success", "partial", "failed"])}
        base["x"] = {"tags": [random.choice(["bug", "feature", "refactor"])]}

    return base

def generate_dataset(total_events: int, ctx_ratio: float, lsp_ratio: float, session_ratio: float, output: str):
    """Generate benchmark dataset with specified distribution."""
    assert abs((ctx_ratio + lsp_ratio + session_ratio) - 1.0) < 0.01

    ctx_count = int(total_events * ctx_ratio)
    lsp_count = int(total_events * lsp_ratio)
    session_count = int(total_events * session_ratio)

    events = []
    base_time = da
