```python
"""Synthetic telemetry data for validation testing."""

import json
from datetime import datetime, timezone
from pathlib import Path

def generate_synthetic_events(n: int = 100) -> list:
    """Generate synthetic events for testing aggregation."""
    events = []
    for i in range(n):
        events.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": f"run_{i}",
            "segment": "/test/segment",
            "cmd": "ctx.search",
            "args": {"query": f"test{i}"},
            "result": {"hits": i % 10},
            "timing_ms": 10 + (i % 100),
            "bytes_read": 1024 * (i % 10),
            "disclosure_mode": ["skeleton", "excerpt", "raw"][i % 3],
        })
    return events

def test_summary_percentile_validation():
    """Validate percentile calculations with synthetic data."""
    from src.infrastructure.telemetry import Telemetry
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_path:
        tmp = Path(tmp_path)
        telemetry = Telemetry(tmp, level="lite")

        # Record synthetic timings
        for i in range(100):
            telemetry.observe("ctx.search", 10 + (i % 100))

        telemetry.flush()

        # Load and validate
        last_run_file = tmp / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        latencies = last_ru
