import json
import time
import os
import hashlib
import re
from pathlib import Path
from typing import Dict

from src.domain.segment_resolver import resolve_segment_ref, get_segment_fingerprint


def _relpath(root: Path, target: Path) -> str:
    """Convert target path to relative path for telemetry.

    If target is inside workspace, returns relative path.
    If target is external, returns external/<hash>-<filename>.
    """
    try:
        # Try to make it relative
        rel = target.relative_to(root)
        return str(rel)
    except ValueError:
        # External file - hash the full path for privacy
        path_hash = hashlib.sha256(str(target).encode()).hexdigest()[:8]
        return f"external/{path_hash}-{target.name}"


def _sanitize_value(value: str) -> str:
    """Redact absolute paths/PII from string values.

    Returns:
        Redacted string if value contains PII patterns, otherwise original value.
    """
    # Posix absolute paths
    if value.startswith(("/Users/", "/home/", "/private/var/", "/mnt/c/", "/mnt/C/")):
        return "<ABS_PATH_REDACTED>"

    # Windows paths (C:\Users\, D:\Users\, etc.)
    if len(value) > 2 and value[1:3] == ":\\" and value[0].isalpha():
        if "Users\\" in value or "users\\" in value:
            return "<ABS_PATH_REDACTED>"

    # File URIs
    if value.startswith("file://"):
        return "<ABS_URI_REDACTED>"

    return value


def _sanitize_event(event: dict) -> dict:
    """Sanitize PII from event dict before persisting.

    Sanitizes common path keys: segment, cwd, path, root, repo_root, file, uri.
    Respects TRIFECTA_PII=allow env var for opt-in bypass.
    """
    # Opt-in bypass for debug/local development
    if os.environ.get("TRIFECTA_PII") == "allow":
        return event

    # Keys that commonly contain paths
    PATH_KEYS = ["segment", "cwd", "path", "root", "repo_root", "file", "uri"]

    # Sanitize args.* path keys if present
    if "args" in event and isinstance(event["args"], dict):
        for key in PATH_KEYS:
            if key in event["args"]:
                value = event["args"][key]
                # Only sanitize string values (avoid crash on Path objects, ints, etc.)
                if isinstance(value, str):
                    event["args"][key] = _sanitize_value(value)

    return event


class Telemetry:
    def __init__(self, root: Path | None = None, level: str = "full"):
        # KILL SWITCH: Detect pre-commit or explicit off mode
        # Priority:
        # 1. PRE_COMMIT=1 or level="off" => Complete NO-OP (no dirs, no writes)
        # 2. TRIFECTA_TELEMETRY_DIR => Write to custom dir (for tests)
        # 3. Default => _ctx/telemetry

        self.level = level
        segment_ref = resolve_segment_ref(root or Path.cwd())
        self.root = segment_ref.root_abs
        self.segment_id = segment_ref.fingerprint
        self.segment_label = segment_ref.slug
        self.run_id = os.environ.get("TRIFECTA_RUN_ID", f"run_{int(time.time())}")
        self.metrics: Dict[str, int] = {}
        self.timings: Dict[str, list] = {}

        # NO-OP mode: complete disable for pre-commit
        # Use TRIFECTA_NO_TELEMETRY instead of PRE_COMMIT to avoid conflicts
        if level == "off" or os.environ.get("TRIFECTA_NO_TELEMETRY") == "1":
            self.level = "off"  # Force off to ensure event() and flush() are NO-OP
            # Set _ctx_dir but do NOT create, do NOT write
            self._ctx_dir = self.root / "_ctx" / "telemetry"
            return  # Early exit, no directory creation, no file writes

        # Override mode: redirect to custom directory (for tests)
        telemetry_dir_override = os.environ.get("TRIFECTA_TELEMETRY_DIR")
        if telemetry_dir_override:
            self._ctx_dir = Path(telemetry_dir_override)
            self._ctx_dir.mkdir(parents=True, exist_ok=True)
            self._normalize_events_file()
            return

        # Default mode: use _ctx/telemetry in segment
        self._ctx_dir = self.root / "_ctx" / "telemetry"
        self._ctx_dir.mkdir(parents=True, exist_ok=True)
        self._normalize_events_file()

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

        # Reserved key protection (PR#1 contract)
        RESERVED_KEYS = {
            "ts",
            "run_id",
            "segment_id",
            "cmd",
            "args",
            "result",
            "timing_ms",
            "warnings",
            "x",
        }
        collisions = set(kwargs.keys()) & RESERVED_KEYS
        if collisions:
            raise ValueError(f"Cannot use reserved keys: {collisions}")

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

        # Sanitize PII before persisting
        payload = _sanitize_event(payload)

        # Write to events.jsonl
        with open(self._ctx_dir / "events.jsonl", "a") as f:
            content = json.dumps(payload)
            if not content.endswith("\n"):
                content += "\n"
            f.write(content)

    def flush(self):
        if self.level == "off":
            return
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

        # Add pack_state if present (for T8.2 consistency)
        if hasattr(self, "pack_state") and self.pack_state:
            summary["pack_state"] = self.pack_state

        content = json.dumps(summary, indent=2)
        if not content.endswith("\n"):
            content += "\n"
        with open(self._ctx_dir / "last_run.json", "w") as f:
            f.write(content)

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

    def _normalize_events_file(self) -> None:
        """Best-effort repair for legacy events lacking required schema fields.

        Keeps telemetry tripwires stable by ensuring every persisted row has:
        run_id, segment_id (8-hex), cmd, args, result, timing_ms, warnings, x.
        """
        events_file = self._ctx_dir / "events.jsonl"
        if not events_file.exists():
            return

        try:
            lines = events_file.read_text().splitlines()
        except OSError:
            return

        normalized_lines: list[str] = []
        changed = False

        for line in lines:
            if not line.strip():
                changed = True
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                changed = True
                continue

            if not isinstance(row, dict):
                changed = True
                continue

            if "run_id" not in row:
                row["run_id"] = self.run_id
                changed = True

            sid = row.get("segment_id")
            if not isinstance(sid, str) or not re.match(r"^[0-9a-f]{8}$", sid):
                row["segment_id"] = self.segment_id
                changed = True

            if "cmd" not in row:
                row["cmd"] = "telemetry.legacy"
                changed = True
            if "args" not in row or not isinstance(row["args"], dict):
                row["args"] = {}
                changed = True
            if "result" not in row or not isinstance(row["result"], dict):
                row["result"] = {}
                changed = True
            if "timing_ms" not in row:
                row["timing_ms"] = 1
                changed = True
            if "warnings" not in row or not isinstance(row["warnings"], list):
                row["warnings"] = []
                changed = True
            if "x" not in row or not isinstance(row["x"], dict):
                row["x"] = {}
                changed = True

            normalized_lines.append(json.dumps(row))

        if changed:
            try:
                events_file.write_text("\n".join(normalized_lines) + ("\n" if normalized_lines else ""))
            except OSError:
                return
