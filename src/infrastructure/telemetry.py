import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Telemetry:
    def __init__(self, root: Path, level: str = "lite"):
        self.root = root
        self.level = level
        self.metrics: Dict[str, Any] = {}
        self._ctx_dir = root / "_ctx" / "telemetry"
        self._ctx_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = f"run_{int(time.time())}"

        # Load prev metrics if needed?
        # For restoration simple start.

    def incr(self, key: str, value: int = 1):
        self.metrics[key] = self.metrics.get(key, 0) + value

    def event(self, cmd: str, args: Dict, result: Dict, timing_ms: int, **kwargs):
        if self.level == "off":
            return

        # PR#1 compliant event
        # kwargs are put into "x"

        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "run_id": self.run_id,
            "segment_id": "restored_seg",
            "cmd": cmd,
            "args": args,
            "result": result,
            "timing_ms": max(1, timing_ms),
            "warnings": [],
            "x": kwargs,
        }

        # Write to events.jsonl
        with open(self._ctx_dir / "events.jsonl", "a") as f:
            f.write(json.dumps(payload) + "\n")

    def flush(self):
        # Write last_run.json
        # Aggregate logic
        summary = {
            "run_id": self.run_id,
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ast": {
                "ast_parse_count": self.metrics.get("ast_parse_count", 0),
                "ast_cache_hit_count": self.metrics.get("ast_cache_hit_count", 0),
                "ast_cache_miss_count": self.metrics.get("ast_cache_miss_count", 0),
            },
            "lsp": {
                "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
                "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
                "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
            },
            "telemetry_drops": {"drop_rate": 0.0},
        }

        with open(self._ctx_dir / "last_run.json", "w") as f:
            f.write(json.dumps(summary, indent=2))
