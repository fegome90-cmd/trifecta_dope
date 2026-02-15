import json
import tempfile
from pathlib import Path

import pytest

from src.application.zero_hit_tracker import ZeroHitTracker, create_zero_hit_tracker


@pytest.fixture
def temp_telemetry_dir(tmp_path):
    tel_dir = tmp_path / "_ctx" / "telemetry"
    tel_dir.mkdir(parents=True)
    events_file = tel_dir / "events.jsonl"
    events_file.write_text("")
    return tel_dir


class TestZeroHitTracker:
    def test_create_tracker(self, temp_telemetry_dir):
        tracker = create_zero_hit_tracker(temp_telemetry_dir)
        assert tracker.telemetry_dir == temp_telemetry_dir
        assert tracker.zero_hits_file == temp_telemetry_dir / "zero_hits.ndjson"

    def test_record_zero_hit_creates_files(self, temp_telemetry_dir):
        tracker = ZeroHitTracker(temp_telemetry_dir)
        tracker.record_zero_hit(
            query="test_query",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
            source="cli",
            build_sha="def456",
            mode="search_only",
            zero_hit_reason="no_packs",
        )

        assert (temp_telemetry_dir / "events.jsonl").exists()
        assert (temp_telemetry_dir / "zero_hits.ndjson").exists()

    def test_record_zero_hit_deduplication(self, temp_telemetry_dir):
        tracker = ZeroHitTracker(temp_telemetry_dir)

        # Record same query twice
        tracker.record_zero_hit(
            query="test_query",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
        )
        tracker.record_zero_hit(
            query="test_query",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
        )

        # Should have one entry with count=2
        with open(temp_telemetry_dir / "zero_hits.ndjson") as f:
            entries = [json.loads(line) for line in f if line.strip()]

        assert len(entries) == 1
        assert entries[0]["count"] == 2

    def test_get_top_zero_hits(self, temp_telemetry_dir):
        tracker = ZeroHitTracker(temp_telemetry_dir)

        # Record different queries
        tracker.record_zero_hit(
            query="query_a",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
        )
        tracker.record_zero_hit(
            query="query_b",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
        )
        tracker.record_zero_hit(
            query="query_b",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
        )
        tracker.record_zero_hit(
            query="query_c",
            segment_fingerprint="abc12345",
            segment_slug="test-segment",
        )

        top = tracker.get_top_zero_hits(limit=2)
        assert len(top) == 2
        assert top[0]["query_preview"] == "query_b"
        assert top[0]["count"] == 2

    def test_query_hash_deterministic(self, temp_telemetry_dir):
        tracker = ZeroHitTracker(temp_telemetry_dir)

        hash1 = tracker._compute_query_hash("test_query")
        hash2 = tracker._compute_query_hash("test_query")

        assert hash1 == hash2
        assert len(hash1) == 12

    def test_redact_long_query(self, temp_telemetry_dir):
        tracker = ZeroHitTracker(temp_telemetry_dir)

        long_query = "a" * 100
        redacted = tracker._redact_query(long_query, max_len=50)

        assert "(+50)" in redacted
