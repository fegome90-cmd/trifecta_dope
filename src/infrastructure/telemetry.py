"""Telemetry module for Trifecta Context (T8)."""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Maximum file size for rotation (5MB)
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024
# Number of rotated files to keep
BACKUP_COUNT = 3

# Reserved keys that cannot be overridden by extra_fields
RESERVED_KEYS = frozenset({
    "ts", "run_id", "segment_id", "cmd", "args", "result",
    "timing_ms", "tokens", "warnings", "x"
})


def _relpath(root: Path, target: Path) -> str:
    """
    Convert absolute path to relative path for telemetry.
    Prevents logging absolute paths or URIs with user/system info.
    
    Args:
        root: Repository/segment root (workspace root)
        target: File path to convert
    
    Returns:
        Relative path string, or external/<hash8>-<name> if outside root
    
    Example:
        >>> _relpath(Path("/workspaces/repo"), Path("/workspaces/repo/src/app.py"))
        'src/app.py'
        >>> _relpath(Path("/workspaces/repo"), Path("/usr/lib/python3.12/typing.py"))
        'external/a3b4c5d6-typing.py'  # hash ensures uniqueness without exposing path
    """
    try:
        return str(target.relative_to(root))
    except ValueError:
        # File outside workspace: hash path for privacy + uniqueness
        path_hash = hashlib.sha256(str(target).encode()).hexdigest()[:8]
        return f"external/{path_hash}-{target.name}"


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
        self.token_usage: Dict[str, Dict[str, int]] = {}
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

    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation: 1 token ≈ 4 characters.
        This is a heuristic approximation, not an exact count.
        """
        if not text:
            return 0
        # Remove extra whitespace for better estimation
        cleaned = " ".join(str(text).split())
        return max(1, len(cleaned) // 4)

    def _estimate_token_usage(
        self, cmd: str, args: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Estimate token usage for this CLI command.
        Returns dict with input_tokens, output_tokens, total_tokens, retrieved_tokens.
        """
        # Estimate input tokens from args
        input_parts = []
        if "query" in args:
            input_parts.append(str(args["query"]))
        if "task" in args:
            input_parts.append(str(args["task"]))
        if "ids" in args:
            input_parts.append(str(args["ids"]))
        input_text = " ".join(input_parts)
        input_tokens = self._estimate_tokens(input_text)

        # Estimate output tokens from result
        output_text = json.dumps(result, default=str)
        output_tokens = self._estimate_tokens(output_text)

        # Retrieved tokens (actual context tokens retrieved, if available)
        retrieved_tokens = result.get("total_tokens", 0)
        if not isinstance(retrieved_tokens, int):
            retrieved_tokens = 0

        total_tokens = input_tokens + output_tokens

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "retrieved_tokens": retrieved_tokens,
        }

    def event(
        self,
        cmd: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
        timing_ms: int,
        warnings: List[str] | None = None,
        **extra_fields: Any,  # NEW: accept arbitrary kwargs
    ) -> None:
        """
        Log a discrete event with optional structured fields.
        
        Args:
            cmd: Command name (e.g., "ctx.search", "ast.parse", "lsp.spawn")
            args: Command arguments (sanitized)
            result: Command result metadata
            timing_ms: Elapsed time in milliseconds (use perf_counter_ns)
            warnings: Optional list of warning messages
            **extra_fields: Additional structured fields (e.g., bytes_read, lsp_state)
        
        Raises:
            ValueError: If extra_fields contains a reserved key
        
        Example:
            telemetry.event(
                "lsp.spawn", 
                {"pyright_binary": "pyright-langserver"}, 
                {"pid": 12345, "status": "ok"},
                42,
                lsp_state="WARMING",  # Goes into payload["x"]["lsp_state"]
                spawn_method="subprocess"  # Goes into payload["x"]["spawn_method"]
            )
        """
        if not self.enabled:
            return

        # Track all event attempts
        self.incr("telemetry_events_attempted", 1)

        if warnings:
            self.warnings.extend(warnings)

        # NEW: Protect reserved keys
        collision = RESERVED_KEYS & extra_fields.keys()
        if collision:
            raise ValueError(
                f"extra_fields contains reserved keys: {collision}. "
                f"Reserved: {RESERVED_KEYS}"
            )

        # Sanitize args for privacy/size
        safe_args = self._sanitize_args(args)

        # Estimate token usage (Opción A: automatic estimation)
        tokens = self._estimate_token_usage(cmd, args, result)

        # Compute stable segment_id (no path leakage)
        segment_id = hashlib.sha256(str(self.segment_path).encode()).hexdigest()[:8]

        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "segment_id": segment_id,  # NEW: stable ID, no absolute path
            "cmd": cmd,
            "args": safe_args,
            "result": result,
            "timing_ms": timing_ms,
            "tokens": tokens,
            "warnings": warnings or [],
            "x": extra_fields,  # NEW: namespace extra fields to prevent future collisions
        }

        try:
            # NEW: _write_jsonl now returns success bool for drop tracking
            if self._write_jsonl("events.jsonl", payload):
                # Track written events
                self.incr("telemetry_events_written", 1)
                # T8.2: Ensure discrete events also record latency for stats
                if timing_ms > 0:
                    self.observe(cmd, timing_ms)
                # Track token usage per command
                if cmd not in self.token_usage:
                    self.token_usage[cmd] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "retrieved_tokens": 0,
                        "count": 0,
                    }
                for key in ["input_tokens", "output_tokens", "total_tokens", "retrieved_tokens"]:
                    self.token_usage[cmd][key] += tokens.get(key, 0)
                self.token_usage[cmd]["count"] += 1
            else:
                # Lock not acquired: track drop
                self.incr("telemetry_lock_skipped", 1)
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
                    "p50_ms": round(sorted(times)[len(times) // 2] / 1000, 3) if times else 0,
                    "p95_ms": round(sorted(times)[int(len(times) * 0.95)] / 1000, 3)
                    if times
                    else 0,
                    "max_ms": round(max(times) / 1000, 3) if times else 0,
                }
                for cmd, times in self.latencies.items()
            }

            # Token usage summary per command
            tokens_summary = {
                cmd: {
                    "count": stats["count"],
                    "total_input_tokens": stats["input_tokens"],
                    "total_output_tokens": stats["output_tokens"],
                    "total_tokens": stats["total_tokens"],
                    "total_retrieved_tokens": stats["retrieved_tokens"],
                    "avg_tokens_per_call": round(stats["total_tokens"] / stats["count"], 1)
                    if stats["count"] > 0
                    else 0,
                }
                for cmd, stats in self.token_usage.items()
            }

            # NEW: AST summary (empty for PR#1, prepared for PR#2)
            ast_summary = {
                "ast_parse_count": self.metrics.get("ast_parse_count", 0),
                "ast_cache_hit_count": self.metrics.get("ast_cache_hit_count", 0),
                "ast_cache_miss_count": self.metrics.get("ast_cache_miss_count", 0),
                "ast_cache_hit_rate": round(
                    self.metrics.get("ast_cache_hit_count", 0) / 
                    max(self.metrics.get("ast_parse_count", 1), 1),
                    3
                ),
            }

            # NEW: LSP summary (empty for PR#1, prepared for PR#2)
            lsp_summary = {
                "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
                "lsp_warming_count": self.metrics.get("lsp_warming_count", 0),
                "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
                "lsp_failed_count": self.metrics.get("lsp_failed_count", 0),
                "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
                "lsp_ready_rate": round(
                    self.metrics.get("lsp_ready_count", 0) / 
                    max(self.metrics.get("lsp_spawn_count", 1), 1),
                    3
                ),
                "lsp_fallback_rate": round(
                    self.metrics.get("lsp_fallback_count", 0) / 
                    max(self.metrics.get("lsp_spawn_count", 1), 1),
                    3
                ),
            }

            # NEW: File read summary by mode (empty for PR#1, prepared for PR#2)
            file_read_summary = {
                "skeleton_bytes": self.metrics.get("file_read_skeleton_bytes_total", 0),
                "excerpt_bytes": self.metrics.get("file_read_excerpt_bytes_total", 0),
                "raw_bytes": self.metrics.get("file_read_raw_bytes_total", 0),
                "total_bytes": (
                    self.metrics.get("file_read_skeleton_bytes_total", 0) +
                    self.metrics.get("file_read_excerpt_bytes_total", 0) +
                    self.metrics.get("file_read_raw_bytes_total", 0)
                ),
            }

            # NEW: Telemetry drops tracking (lossy fcntl model)
            attempted = self.metrics.get("telemetry_events_attempted", 0)
            written = self.metrics.get("telemetry_events_written", 0)
            lock_skipped = self.metrics.get("telemetry_lock_skipped", 0)
            telemetry_drops = {
                "lock_skipped": lock_skipped,
                "attempted": attempted,
                "written": written,
                "drop_rate": round(lock_skipped / max(attempted, 1), 4),
            }

            run_summary = {
                "run_id": self.run_id,
                "ts": datetime.now(timezone.utc).isoformat(),
                "metrics_delta": self.metrics,
                "latencies": latency_summary,
                "tokens": tokens_summary,
                "ast": ast_summary,              # NEW (PR#1: empty, PR#2: populated)
                "lsp": lsp_summary,              # NEW (PR#1: empty, PR#2: populated)
                "file_read": file_read_summary,  # NEW (PR#1: empty, PR#2: populated)
                "telemetry_drops": telemetry_drops,  # NEW: track lossy fcntl drops
                "top_warnings": self.warnings[:5],  # Top 5 warnings
                "pack_state": {
                    "pack_sha": self.pack_sha,
                    "pack_mtime": self.pack_mtime,
                    **(
                        {}
                        if self.stale_detected is None
                        else {"stale_detected": self.stale_detected}
                    ),
                },
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
                    safe[k] = v[:120]  # Truncate task
                else:
                    safe[k] = v
            # Skip unknown args for safety
        return safe

    def _write_jsonl(self, filename: str, data: Dict[str, Any]) -> bool:
        """
        Append to JSONL with rotation and locking.
        
        Returns:
            True if write succeeded, False if lock was busy (for drop tracking)
        """
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
                    return False  # Signal drop occurred

                # Lock acquired, write and unlock
                f.write(json.dumps(data) + "\n")
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return True  # Write succeeded
        except Exception as e:
            logging.warning(f"Failed to write to {filename}: {e}")
            return False

    def _rotate_if_needed(self, path: Path) -> None:
        """Simple rotation: .1.jsonl, .2.jsonl, .3.jsonl"""
        if not path.exists() or path.stat().st_size < MAX_LOG_SIZE_BYTES:
            return

        # Shift existing backups
        for i in range(BACKUP_COUNT - 1, 0, -1):
            src = path.with_suffix(f".{i}.jsonl")  # e.g. events.2.jsonl
            dst = path.with_suffix(f".{i + 1}.jsonl")  # e.g. events.3.jsonl
            if src.exists():
                src.rename(dst)

        # Move current to .1
        path.rename(path.with_suffix(".1.jsonl"))
