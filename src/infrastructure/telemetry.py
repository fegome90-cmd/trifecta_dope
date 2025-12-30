"""Telemetry module for Trifecta Context (T8)."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.domain.models import TrifectaConfig

# Maximum file size for rotation (5MB)
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024
# Number of rotated files to keep
BACKUP_COUNT = 3


class Telemetry:
    """
    Local-first, lightweight telemetry system.
    
    Stores data in <segment>/_ctx/telemetry/
    - events.jsonl: Detailed event log (rotated)
    - metrics.json: Aggregated counters
    - last_run.json: Summary of the last execution
    """

    def __init__(self, segment_path: Path, level: str = "lite", run_id: str = ""):
        self.segment_path = segment_path
        self.telemetry_dir = segment_path / "_ctx" / "telemetry"
        self.level = level
        self.run_id = run_id or f"run_{int(time.time())}"
        self.enabled = level.lower() != "off"
        
        # In-memory aggregation for this run
        self.metrics: Dict[str, int] = {}
        self.latencies: Dict[str, List[int]] = {}
        self.warnings: List[str] = []
        
        # Pack state tracking
        self.pack_sha: Optional[str] = None
        self.pack_mtime: Optional[float] = None
        self.stale_detected: Optional[bool] = None
        
        if self.enabled:
            try:
                self.telemetry_dir.mkdir(parents=True, exist_ok=True)
                self._compute_pack_state()
            except Exception as e:
                # Fail safe - disable if cannot write
                logging.warning(f"Failed to create telemetry dir: {e}")
                self.enabled = False
    
    def _compute_pack_state(self) -> None:
        """Compute pack SHA and mtime for stale detection."""
        pack_path = self.segment_path / "_ctx" / "context_pack.json"
        if pack_path.exists():
            import hashlib
            try:
                content = pack_path.read_bytes()
                self.pack_sha = hashlib.sha256(content).hexdigest()[:16]  # Short hash
                self.pack_mtime = pack_path.stat().st_mtime
            except Exception:
                pass  # Non-critical

    def event(
        self, 
        cmd: str, 
        args: Dict[str, Any], 
        result: Dict[str, Any], 
        timing_ms: int, 
        warnings: List[str] | None = None
    ) -> None:
        """Log a discrete event."""
        if not self.enabled:
            return

        if warnings:
            self.warnings.extend(warnings)

        # Sanitize args for privacy/size
        safe_args = self._sanitize_args(args)
        
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "segment": str(self.segment_path),
            "cmd": cmd,
            "args": safe_args,
            "result": result,
            "timing_ms": timing_ms,
            "warnings": warnings or []
        }

        try:
            self._write_jsonl("events.jsonl", payload)
        except Exception:
            pass  # Never break the app

    def incr(self, name: str, n: int = 1) -> None:
        """Increment a counter."""
        if not self.enabled:
            return
        self.metrics[name] = self.metrics.get(name, 0) + n

    def observe(self, cmd: str, ms: int) -> None:
        """Record latency observation in microseconds."""
        if not self.enabled:
            return
        if cmd not in self.latencies:
            self.latencies[cmd] = []
        # Convert ms to microseconds for precision
        self.latencies[cmd].append(ms * 1000)

    def flush(self) -> None:
        """Persist aggregated metrics and run summary."""
        if not self.enabled:
            return

        try:
            # 1. Update cumulative metrics.json
            metrics_path = self.telemetry_dir / "metrics.json"
            current_metrics = {}
            if metrics_path.exists():
                try:
                    current_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
            
            # Merge in-memory metrics
            for k, v in self.metrics.items():
                current_metrics[k] = current_metrics.get(k, 0) + v
            
            metrics_path.write_text(json.dumps(current_metrics, indent=2), encoding="utf-8")

            # 2. Write last_run.json
            last_run_path = self.telemetry_dir / "last_run.json"
            latency_summary = {
                cmd: {
                    "count": len(times),
                    "p50_ms": round(sorted(times)[len(times)//2] / 1000, 3) if times else 0,
                    "p95_ms": round(sorted(times)[int(len(times)*0.95)] / 1000, 3) if times else 0,
                    "max_ms": round(max(times) / 1000, 3) if times else 0
                }
                for cmd, times in self.latencies.items()
            }
            
            run_summary = {
                "run_id": self.run_id,
                "ts": datetime.now(timezone.utc).isoformat(),
                "metrics_delta": self.metrics,
                "latencies": latency_summary,
                "top_warnings": self.warnings[:5],  # Top 5 warnings
                "pack_state": {
                    "pack_sha": self.pack_sha,
                    "pack_mtime": self.pack_mtime,
                    **({} if self.stale_detected is None else {"stale_detected": self.stale_detected})
                }
            }
            
            last_run_path.write_text(json.dumps(run_summary, indent=2), encoding="utf-8")
            
        except Exception as e:
            logging.warning(f"Telemetry flush failed: {e}")

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate and sanitize arguments based on level."""
        safe = {}
        for k, v in args.items():
            if k == "query" and isinstance(v, str):
                safe[k] = v[:120]  # Truncate query
            elif k in ["ids", "segment", "limit", "mode", "budget_token_est", "task"]:
                if k == "task" and isinstance(v, str):
                     safe[k] = v[:120] # Truncate task
                else:
                    safe[k] = v
            # Skip unknown args for safety
        return safe

    def _write_jsonl(self, filename: str, data: Dict[str, Any]) -> None:
        """Append to JSONL with rotation and locking."""
        path = self.telemetry_dir / filename
        self._rotate_if_needed(path)
        
        # POSIX file locking (fail-safe: skip write if lock busy)
        import fcntl
        try:
            with open(path, "a", encoding="utf-8") as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    # Lock busy: skip write to avoid corruption
                    if not hasattr(self, '_lock_warning_shown'):
                        import sys
                        print("Telemetry skipped: lock busy", file=sys.stderr)
                        self._lock_warning_shown = True
                        self.warnings.append("telemetry_lock_skipped")
                    return  # Skip write
                
                # Lock acquired, write and unlock
                f.write(json.dumps(data) + "\n")
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logging.warning(f"Failed to write to {filename}: {e}")

    def _rotate_if_needed(self, path: Path) -> None:
        """Simple rotation: .1.jsonl, .2.jsonl, .3.jsonl"""
        if not path.exists() or path.stat().st_size < MAX_LOG_SIZE_BYTES:
            return

        # Shift existing backups
        for i in range(BACKUP_COUNT - 1, 0, -1):
            src = path.with_suffix(f".{i}.jsonl") # e.g. events.2.jsonl
            dst = path.with_suffix(f".{i+1}.jsonl") # e.g. events.3.jsonl
            if src.exists():
                src.rename(dst)
        
        # Move current to .1
        path.rename(path.with_suffix(".1.jsonl"))
