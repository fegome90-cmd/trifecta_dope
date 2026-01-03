import json
import pytest
import re
from src.infrastructure.telemetry import Telemetry
from src.infrastructure.segment_utils import resolve_segment_root, compute_segment_id


def test_segment_id_is_hash8():
    """Verify segment_id format in events.jsonl"""
    root = resolve_segment_root()
    events_path = root / "_ctx" / "telemetry" / "events.jsonl"

    if not events_path.exists():
        pytest.skip("No events.jsonl found")

    lines = events_path.read_text().splitlines()
    if not lines:
        return  # Valid empty

    for line in lines:
        data = json.loads(line)
        seg_id = data.get("segment_id")
        assert seg_id, "segment_id missing in event"
        assert re.match(r"^[0-9a-f]{8}$", seg_id), f"Invalid segment_id format: {seg_id}"


def test_segment_id_singleton_per_run():
    """Verify single segment_id per run_id"""
    root = resolve_segment_root()
    events_path = root / "_ctx" / "telemetry" / "events.jsonl"

    if not events_path.exists():
        pytest.skip("No events.jsonl found")

    lines = events_path.read_text().splitlines()
    run_map = {}

    for line in lines:
        data = json.loads(line)
        rid = data.get("run_id")
        sid = data.get("segment_id")

        if rid not in run_map:
            run_map[rid] = sid
        else:
            assert run_map[rid] == sid, f"Mixed segment_ids in run {rid}: {run_map[rid]} vs {sid}"


def test_resolve_root_consistency():
    """Verify resolve_segment_root matches expected repo root"""
    root = resolve_segment_root()
    assert (root / "README.md").exists()
    assert (root / "pyproject.toml").exists()

    # Verify compute matches
    sid = compute_segment_id(root)
    assert len(sid) == 8

    tsc = Telemetry(root)
    assert tsc.segment_id == sid
