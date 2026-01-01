import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional


import hashlib
from src.infrastructure.segment_utils import resolve_segment_root, compute_segment_id


class Telemetry:
    def __init__(self, root: Path = None, level: str = "full"):
        self.root = resolve_segment_root(root or Path.cwd())
        self._ctx_dir = self.root / "_ctx" / "telemetry"
        self._ctx_dir.mkdir(parents=True, exist_ok=True)
        self.metrics: Dict[str, int] = {}
        self.timings: Dict[str, list] = {}  # For observe() latency tracking
        self.level = level
        self.run_id = f"run_{int(time.time())}"

        # Phase 3 Audit: segment_id hash 8 chars (Unified)
        self.segment_id = compute_segment_id(self.root)
        self.segment_label = (
            root.name
        )  # Keep original name logic for label if needed contextually, or self.root.name

        # Load prev metrics if needed?
        # For restoration simple start.

    def incr(self, key: str, val: int = 1):
        self.metrics[key] = self.metrics.get(key, 0) + val

    def observe(self, cmd: str, timing_ms: int):
        """Record a timing observation for latency aggregation."""
        if cmd not in self.timings:
            self.timings[cmd] = []
        self.timings[cmd].append(timing_ms)

    def event(self, cmd: str, args: Dict, result: Dict, timing_ms: int, **kwargs):
        if self.level == "off":
            return

        # PR#1 compliant event
        # kwargs are put into "x"

        def _summarize_timings(vals: list[int]):
            if not vals:
                return {}
            sorted_vals = sorted(vals)
            n = len(sorted_vals)
            return {
                "count": n,
                "p50_ms": sorted_vals[int(n * 0.5)],
                "p95_ms": sorted_vals[int(n * 0.95)],
                "max_ms": sorted_vals[-1],
            }

        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "run_id": self.run_id,
            "segment_id": self.segment_id,
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
            "segment_id": self.segment_id,
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
                "lsp_request_count": self.metrics.get("lsp_request_count", 0),
            },
            "telemetry_drops": {"drop_rate": 0.0},
        }

        # Add latencies if any timings were observed
        if self.timings:
            latencies = {}
            for cmd, vals in self.timings.items():
                stats = self._compute_stats(vals)
                if stats:
                    latencies[cmd] = stats
            if latencies:
                summary["latencies"] = latencies

        with open(self._ctx_dir / "last_run.json", "w") as f:
            f.write(json.dumps(summary, indent=2))

    def _compute_stats(self, vals: list[int]):
        """Compute p50, p95, max from timing values."""
        if not vals:
            return {}
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        return {
            "count": n,
            "p50_ms": sorted_vals[int(n * 0.5)],
            "p95_ms": sorted_vals[int(n * 0.95)],
            "max_ms": sorted_vals[-1],
        }
