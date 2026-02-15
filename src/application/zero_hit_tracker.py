import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ZeroHitRecord:
    """Structured zero-hit record for tracking."""

    query_hash: str
    query_preview: str
    query_len: int
    segment_fingerprint: str
    segment_slug: str
    source: str
    build_sha: str
    mode: str
    zero_hit_reason: Optional[str]
    count: int = 1


class ZeroHitTracker:
    """Track zero-hit queries with deduplication.

    Emits events to events.jsonl and maintains deduplicated aggregated file.
    """

    TRACKED_FIELDS = [
        "query_hash",
        "query_preview",
        "query_len",
        "segment_fingerprint",
        "segment_slug",
        "source",
        "build_sha",
        "mode",
        "zero_hit_reason",
    ]

    def __init__(self, telemetry_dir: Path):
        self.telemetry_dir = telemetry_dir
        self.zero_hits_file = telemetry_dir / "zero_hits.ndjson"

    def _compute_query_hash(self, query: str) -> str:
        """Compute short hash for deduplication."""
        return hashlib.sha256(query.encode()).hexdigest()[:12]

    def _redact_query(self, query: str, max_len: int = 50) -> str:
        """Redact query for privacy, keeping length info."""
        if len(query) <= max_len:
            return query
        return f"{query[:max_len]}...(+{len(query) - max_len})"

    def record_zero_hit(
        self,
        query: str,
        segment_fingerprint: str,
        segment_slug: str,
        source: str = "unknown",
        build_sha: str = "unknown",
        mode: str = "search_only",
        zero_hit_reason: Optional[str] = None,
        limit: int = 10,
    ) -> None:
        """Record a zero-hit event.

        Args:
            query: Original query string
            segment_fingerprint: Unique segment identifier
            segment_slug: Human-readable segment name
            source: Caller source (cli, lsp, hook, etc.)
            build_sha: Build identifier
            mode: Search mode
            zero_hit_reason: Classified reason if known
            limit: Top_k requested
        """
        query_hash = self._compute_query_hash(query)
        query_preview = self._redact_query(query)
        query_len = len(query)

        record = ZeroHitRecord(
            query_hash=query_hash,
            query_preview=query_preview,
            query_len=query_len,
            segment_fingerprint=segment_fingerprint,
            segment_slug=segment_slug,
            source=source,
            build_sha=build_sha,
            mode=mode,
            zero_hit_reason=zero_hit_reason,
            count=1,
        )

        self._append_event(record)
        self._update_aggregated(record)

    def _append_event(self, record: ZeroHitRecord) -> None:
        """Append raw event to events.jsonl."""
        events_file = self.telemetry_dir / "events.jsonl"
        event = {
            "ts": self._get_timestamp(),
            "cmd": "ctx.search.zero_hit",
            "args": {
                "query_hash": record.query_hash,
                "query_preview": record.query_preview,
                "query_len": record.query_len,
                "limit": 10,
            },
            "result": {"hits": 0},
            "timing_ms": 1,
            "x": {
                "segment_fingerprint": record.segment_fingerprint,
                "segment_slug": record.segment_slug,
                "source": record.source,
                "build_sha": record.build_sha,
                "mode": record.mode,
                "zero_hit_reason": record.zero_hit_reason,
            },
        }
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _update_aggregated(self, record: ZeroHitRecord) -> None:
        """Update deduplicated aggregated file."""
        key = (
            f"{record.segment_fingerprint}:{record.query_hash}:"
            f"{record.segment_slug}:{record.source}"
        )

        existing = {}
        if self.zero_hits_file.exists():
            try:
                with open(self.zero_hits_file) as f:
                    for line in f:
                        if line.strip():
                            r = json.loads(line)
                            k = r.get("key")
                            if k:
                                existing[k] = r
            except (json.JSONDecodeError, IOError):
                existing = {}

        if key in existing:
            existing[key]["count"] += 1
            existing[key]["last_seen"] = self._get_timestamp()
        else:
            existing[key] = {
                "key": key,
                "query_hash": record.query_hash,
                "query_preview": record.query_preview,
                "query_len": record.query_len,
                "segment_fingerprint": record.segment_fingerprint,
                "segment_slug": record.segment_slug,
                "source": record.source,
                "build_sha": record.build_sha,
                "mode": record.mode,
                "zero_hit_reason": record.zero_hit_reason,
                "count": 1,
                "first_seen": self._get_timestamp(),
                "last_seen": self._get_timestamp(),
            }

        with open(self.zero_hits_file, "w") as f:
            for rec in existing.values():
                f.write(json.dumps(rec) + "\n")

    def _get_timestamp(self) -> str:
        """Get ISO timestamp."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def get_top_zero_hits(self, limit: int = 10) -> list[dict]:
        """Get top zero-hit queries by count.

        Args:
            limit: Number of results to return

        Returns:
            List of zero-hit records sorted by count
        """
        if not self.zero_hits_file.exists():
            return []

        results = []
        try:
            with open(self.zero_hits_file) as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
        except (json.JSONDecodeError, IOError):
            return []

        results.sort(key=lambda x: x.get("count", 0), reverse=True)
        return results[:limit]


def create_zero_hit_tracker(telemetry_dir: Path) -> ZeroHitTracker:
    """Factory function to create ZeroHitTracker."""
    return ZeroHitTracker(telemetry_dir)
