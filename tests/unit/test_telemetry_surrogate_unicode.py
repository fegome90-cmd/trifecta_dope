"""Regression test: telemetry must handle surrogate characters from file reads.

Root cause: json.dumps() output containing lone surrogate code points (U+DC80-U+DFFF)
crashes when written to UTF-8 files. Surrogates appear from errors='replace' or
'surrogateescape' file reads, or from external tools writing to events.jsonl.

Fix: _strip_surrogates() recursively replaces lone surrogates with U+FFFD before
json.dumps() at all three serialization sites in telemetry.py (lines 210, 252, 331).
"""

import json

import pytest

from src.infrastructure.telemetry import Telemetry


@pytest.fixture
def tel_with_dir(tmp_path, monkeypatch):
    """Create a Telemetry instance writing to a temp dir."""
    monkeypatch.setenv("TRIFECTA_TELEMETRY_DIR", str(tmp_path / "tel"))
    return Telemetry()


class TestSurrogateUnicodeInEvent:
    """event() must not crash on surrogate characters in args/result."""

    def test_surrogate_in_args_replaced(self, tel_with_dir):
        """Surrogate chars in event args should be replaced with U+FFFD."""
        tel_with_dir.event(
            cmd="ctx.stats",
            args={"file_content": "hello \udcff world"},
            result={"status": "ok"},
            timing_ms=42,
        )
        events_file = tel_with_dir._ctx_dir / "events.jsonl"
        lines = events_file.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["cmd"] == "ctx.stats"
        # Surrogate should be replaced with U+FFFD
        assert "\ufffd" in row["args"]["file_content"]
        assert "\udcff" not in row["args"]["file_content"]

    def test_surrogate_in_result_replaced(self, tel_with_dir):
        """Surrogate chars in event result should be replaced with U+FFFD."""
        tel_with_dir.event(
            cmd="ctx.build",
            args={},
            result={"output": "data: \udc80 \udcff \udc9f"},
            timing_ms=100,
        )
        events_file = tel_with_dir._ctx_dir / "events.jsonl"
        lines = events_file.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert "\ufffd" in row["result"]["output"]
        assert "\udc80" not in row["result"]["output"]

    def test_surrogate_in_kwargs_replaced(self, tel_with_dir):
        """Surrogate chars in extra kwargs (x field) should be replaced."""
        tel_with_dir.event(
            cmd="ctx.search",
            args={"query": "test"},
            result={"hits": 1},
            timing_ms=10,
            snippet="\udcff snippet text",
        )
        events_file = tel_with_dir._ctx_dir / "events.jsonl"
        lines = events_file.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert "\ufffd" in row["x"]["snippet"]

    def test_no_surrogates_passes_through(self, tel_with_dir):
        """Normal unicode content should pass through unchanged."""
        tel_with_dir.event(
            cmd="ctx.search",
            args={"query": "búsqueda café"},
            result={"hits": 3},
            timing_ms=10,
        )
        events_file = tel_with_dir._ctx_dir / "events.jsonl"
        row = json.loads(events_file.read_text().strip())
        assert row["args"]["query"] == "búsqueda café"


class TestSurrogateUnicodeInFlush:
    """flush() must not crash when metrics contain surrogate characters."""

    def test_flush_with_surrogate_in_pack_state(self, tel_with_dir):
        """pack_state with surrogate chars should be sanitized in last_run.json."""
        tel_with_dir.pack_state = {"summary": "build \udcff complete"}
        tel_with_dir.flush()
        last_run_file = tel_with_dir._ctx_dir / "last_run.json"
        data = json.loads(last_run_file.read_text())
        assert "\ufffd" in data["pack_state"]["summary"]


class TestSurrogateUnicodeInNormalize:
    """_normalize_events_file() must not crash on legacy events with surrogates."""

    def test_normalize_replaces_surrogates(self, tel_with_dir):
        """Legacy events with surrogate chars should have surrogates replaced."""
        events_file = tel_with_dir._ctx_dir / "events.jsonl"
        # Write a legacy event with surrogate chars (minimal fields)
        legacy_event = {"cmd": "ctx.stats", "result": {"data": "\udcff broken"}}
        events_file.write_text(json.dumps(legacy_event) + "\n")

        # Re-create telemetry to trigger _normalize_events_file
        tel2 = Telemetry.__new__(Telemetry)
        tel2.level = "full"
        tel2.run_id = "test_run"
        tel2.segment_id = "aabbccdd"
        tel2._ctx_dir = tel_with_dir._ctx_dir
        tel2._normalize_events_file()

        lines = events_file.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert "\ufffd" in row["result"]["data"]
        assert "\udcff" not in row["result"]["data"]

    def test_normalize_surrogates_in_nested_structures(self, tel_with_dir):
        """Surrogates in deeply nested dicts and lists should all be replaced."""
        events_file = tel_with_dir._ctx_dir / "events.jsonl"
        legacy_event = {
            "cmd": "legacy",
            "args": {"nested": {"deep": ["\udc80", "ok", "\udcff"]}},
            "result": {"items": [{"val": "\udc9f"}]},
        }
        events_file.write_text(json.dumps(legacy_event) + "\n")

        tel2 = Telemetry.__new__(Telemetry)
        tel2.level = "full"
        tel2.run_id = "test_run"
        tel2.segment_id = "aabbccdd"
        tel2._ctx_dir = tel_with_dir._ctx_dir
        tel2._normalize_events_file()

        row = json.loads(events_file.read_text().strip())
        assert row["args"]["nested"]["deep"] == ["\ufffd", "ok", "\ufffd"]
        assert row["result"]["items"][0]["val"] == "\ufffd"
