"""
Unit tests for Field Exercises anchor metrics extractor.

Tests the extraction logic using fixture telemetry events.
"""

import json
from pathlib import Path

import pytest

from eval.scripts.extract_anchor_metrics import (
    analyze_linter_events,
    extract_anchor_metrics,
    load_telemetry_events,
)


@pytest.fixture
def sample_off_event():
    """Sample ctx.search event with linter disabled (OFF mode)."""
    return {
        "ts": "2026-01-06T13:00:00-0300",
        "run_id": "run_test_off",
        "segment_id": "test_segment",
        "cmd": "ctx.search",
        "args": {
            "query_preview": "testing",
            "query_hash": "abc123",
            "query_len": 7,
            "limit": 10,
        },
        "result": {
            "hits": 5,
            "returned_ids": ["id1", "id2", "id3", "id4", "id5"],
        },
        "timing_ms": 50,
    }


@pytest.fixture
def sample_on_event_expanded():
    """Sample ctx.search event with linter enabled and expansion (ON mode)."""
    return {
        "ts": "2026-01-06T13:01:00-0300",
        "run_id": "run_test_on",
        "segment_id": "test_segment",
        "cmd": "ctx.search",
        "args": {
            "query_preview": "sync",
            "query_hash": "def456",
            "query_len": 4,
            "limit": 10,
            "alias_expanded": False,
            "alias_terms_count": 0,
            "alias_keys_used": [],
            "linter_query_class": "vague",
            "linter_expanded": True,
            "linter_added_strong_count": 2,
            "linter_added_weak_count": 0,
            "linter_reasons": ["vague_default_boost"],
        },
        "result": {
            "hits": 8,
            "returned_ids": ["id1", "id2", "id3", "id4", "id5", "id6", "id7", "id8"],
        },
        "timing_ms": 75,
    }


@pytest.fixture
def sample_on_event_not_expanded():
    """Sample ctx.search event with linter enabled but no expansion (ON mode)."""
    return {
        "ts": "2026-01-06T13:02:00-0300",
        "run_id": "run_test_on",
        "segment_id": "test_segment",
        "cmd": "ctx.search",
        "args": {
            "query_preview": "ValidateContextPackUseCase",
            "query_hash": "ghi789",
            "query_len": 25,
            "limit": 10,
            "alias_expanded": False,
            "alias_terms_count": 0,
            "alias_keys_used": [],
            "linter_query_class": "guided",
            "linter_expanded": False,
            "linter_added_strong_count": 0,
            "linter_added_weak_count": 0,
            "linter_reasons": [],
        },
        "result": {
            "hits": 10,
            "returned_ids": [f"id{i}" for i in range(10)],
        },
        "timing_ms": 30,
    }


def test_extract_anchor_metrics_separates_off_on(
    sample_off_event, sample_on_event_expanded, sample_on_event_not_expanded
):
    """Test that extractor correctly separates OFF and ON mode events."""
    events = [sample_off_event, sample_on_event_expanded, sample_on_event_not_expanded]

    metrics = extract_anchor_metrics(events)

    assert "off_mode" in metrics
    assert "on_mode" in metrics
    assert metrics["off_events_count"] == 1
    assert metrics["on_events_count"] == 2
    assert metrics["total_search_events"] == 3


def test_extract_anchor_metrics_off_mode_calculations(sample_off_event):
    """Test OFF mode metric calculations."""
    events = [sample_off_event]

    metrics = extract_anchor_metrics(events)

    off = metrics["off_mode"]
    assert off["total_queries"] == 1
    assert off["total_hits"] == 5
    assert off["avg_hits"] == 5.0
    assert off["zero_hit_count"] == 0


def test_extract_anchor_metrics_on_mode_calculations(
    sample_on_event_expanded, sample_on_event_not_expanded
):
    """Test ON mode metric calculations including anchor usage."""
    events = [sample_on_event_expanded, sample_on_event_not_expanded]

    metrics = extract_anchor_metrics(events)

    on = metrics["on_mode"]
    assert on["total_queries"] == 2
    assert on["total_hits"] == 18  # 8 + 10
    assert on["avg_hits"] == 9.0
    assert on["zero_hit_count"] == 0

    # Anchor metrics
    assert on["anchor_usage_count"] == 1  # Only one expanded
    assert on["anchor_usage_rate"] == 50.0  # 1/2 = 50%
    assert on["total_strong_anchors_added"] == 2
    assert on["total_weak_anchors_added"] == 0
    assert on["avg_strong_per_query"] == 1.0  # 2/2


def test_extract_anchor_metrics_delta_hits_when_expanded(
    sample_on_event_expanded, sample_on_event_not_expanded
):
    """Test delta calculation for hits when expanded vs not expanded."""
    events = [sample_on_event_expanded, sample_on_event_not_expanded]

    metrics = extract_anchor_metrics(events)

    on = metrics["on_mode"]
    # Expanded: 8 hits (avg = 8.0)
    # Not expanded: 10 hits (avg = 10.0)
    # Delta: 8.0 - 10.0 = -2.0
    assert on["avg_hits_when_expanded"] == 8.0
    assert on["avg_hits_when_not_expanded"] == 10.0
    assert on["delta_hits_when_expanded"] == -2.0


def test_extract_anchor_metrics_query_class_distribution(
    sample_on_event_expanded, sample_on_event_not_expanded
):
    """Test query class distribution counting."""
    events = [sample_on_event_expanded, sample_on_event_not_expanded]

    metrics = extract_anchor_metrics(events)

    on = metrics["on_mode"]
    distribution = on["query_class_distribution"]

    assert distribution["vague"] == 1
    assert distribution["guided"] == 1
    assert len(distribution) == 2


def test_extract_anchor_metrics_zero_hit_handling():
    """Test handling of zero-hit queries."""
    zero_hit_event = {
        "cmd": "ctx.search",
        "args": {
            "linter_query_class": "vague",
            "linter_expanded": True,
            "linter_added_strong_count": 1,
            "linter_added_weak_count": 0,
        },
        "result": {"hits": 0, "returned_ids": []},
    }

    events = [zero_hit_event]
    metrics = extract_anchor_metrics(events)

    on = metrics["on_mode"]
    assert on["zero_hit_count"] == 1
    assert on["zero_hit_rate"] == 100.0
    assert on["total_hits"] == 0


def test_extract_anchor_metrics_no_search_events():
    """Test error handling when no ctx.search events found."""
    non_search_events = [
        {"cmd": "ctx.build", "args": {}, "result": {}},
        {"cmd": "ctx.sync", "args": {}, "result": {}},
    ]

    metrics = extract_anchor_metrics(non_search_events)

    assert "error" in metrics
    assert "No ctx.search events found" in metrics["error"]
    assert metrics["total_events"] == 2


def test_load_telemetry_events_from_jsonl(tmp_path):
    """Test loading events from JSONL file."""
    jsonl_path = tmp_path / "test_events.jsonl"

    events = [
        {"cmd": "ctx.search", "args": {}, "result": {"hits": 5}},
        {"cmd": "ctx.build", "args": {}, "result": {}},
    ]

    with open(jsonl_path, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    loaded = load_telemetry_events(jsonl_path)

    assert len(loaded) == 2
    assert loaded[0]["cmd"] == "ctx.search"
    assert loaded[1]["cmd"] == "ctx.build"


def test_load_telemetry_events_skips_malformed_lines(tmp_path):
    """Test that loader skips malformed JSON lines."""
    jsonl_path = tmp_path / "test_malformed.jsonl"

    with open(jsonl_path, "w") as f:
        f.write('{"cmd": "ctx.search", "args": {}}\n')
        f.write("INVALID JSON LINE\n")
        f.write('{"cmd": "ctx.build", "args": {}}\n')

    loaded = load_telemetry_events(jsonl_path)

    assert len(loaded) == 2  # Skipped malformed line
    assert loaded[0]["cmd"] == "ctx.search"
    assert loaded[1]["cmd"] == "ctx.build"
