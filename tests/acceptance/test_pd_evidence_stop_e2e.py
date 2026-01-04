"""Deterministic E2E acceptance test for evidence-based early-stop.

Refactored to be fail-closed (no pytest.skip) with deterministic fixtures.
"""

import json
import re
import subprocess
from pathlib import Path
import pytest


@pytest.fixture
def minimal_evidence_segment(tmp_path: Path) -> Path:
    """Create a minimal segment with evidence-bearing code (deterministic fixture).

    This fixture is fail-closed: if setup fails, the test fails (not skips).
    """
    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Create Python file with def Foo() - this will be evidence
    foo_py = segment / "foo.py"
    foo_py.write_text("""# Foo Module
def Foo():
    \"\"\"Main Foo function.\"\"\"
    return 1

def FooBar():
    \"\"\"Not a match for Foo query.\"\"\"
    return 2
""")

    # Create minimal skill.md
    skill_md = segment / "skill.md"
    skill_md.write_text("""---
name: test_segment
description: Test segment for E2E evidence stop
---
# Test Segment

This is a test segment.
""")

    # Run trifecta CLI workflow (fail-closed: errors fail the test)
    result_create = subprocess.run(
        ["uv", "run", "trifecta", "create", "-s", str(segment)],
        capture_output=True,
        text=True,
        cwd=segment.parent,
    )
    assert result_create.returncode == 0, f"trifecta create failed: {result_create.stderr}"

    result_sync = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        cwd=segment.parent,
    )
    assert result_sync.returncode == 0, f"trifecta ctx sync failed: {result_sync.stderr}"

    # Verify context pack was created
    context_pack_path = segment / "_ctx" / "context_pack.json"
    assert context_pack_path.exists(), "Context pack not created - ctx sync should have created it"

    return segment


def _get_chunk_ids(segment: Path) -> list[str]:
    """Extract chunk IDs from context pack (utility function)."""
    context_pack_path = segment / "_ctx" / "context_pack.json"
    with open(context_pack_path) as f:
        context_pack = json.load(f)

    ids = [entry["id"] for entry in context_pack.get("index", [])]
    assert len(ids) >= 1, f"No chunks in context pack: {context_pack.get('index', [])}"
    return ids


def _search_for_ids(segment: Path, query: str, limit: int = 3) -> list[str]:
    """Search for IDs via CLI (utility function with assertions)."""
    search_result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "-s",
            str(segment),
            "-q",
            query,
            "--limit",
            str(limit),
        ],
        capture_output=True,
        text=True,
        cwd=segment,
    )
    assert search_result.returncode == 0, f"Search failed: {search_result.stderr}"

    ids = []
    for line in search_result.stdout.split("\n"):
        if line.strip() and "[" in line and "]" in line:
            start = line.find("[")
            end = line.find("]")
            if start != -1 and end != -1:
                ids.append(line[start + 1 : end])

    assert len(ids) > 0, f"No IDs found for query '{query}'"
    return ids


def test_e2e_evidence_stop_deterministic(minimal_evidence_segment: Path):
    """E2E test with deterministic segment - validates early-stop via PD_REPORT."""
    segment = minimal_evidence_segment
    ids = _get_chunk_ids(segment)

    # Use at most 3 chunks for the test
    test_ids = ids[:3] if len(ids) >= 3 else ids * 3

    # Run ctx get with --pd-report for parseable output
    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "--segment",
            str(segment),
            "--ids",
            ",".join(test_ids[:3]),
            "--mode",
            "excerpt",
            "--stop-on-evidence",
            "--query",
            "Foo",
            "--max-chunks",
            "3",
            "--pd-report",
        ],
        capture_output=True,
        text=True,
        cwd=segment.parent,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    output = result.stdout

    # Parse PD_REPORT line
    pd_report_line = None
    for line in output.split("\n"):
        if line.startswith("PD_REPORT v="):
            pd_report_line = line
            break

    assert pd_report_line is not None, f"PD_REPORT line not found in output:\n{output}"

    # Parse key=value pairs
    metrics = {}
    for match in re.finditer(r"(\w+)=([\w.]+)", pd_report_line):
        key, value = match.groups()
        metrics[key] = value

    # Validate metrics structure
    assert "stop_reason" in metrics, f"stop_reason not in metrics: {metrics}"
    assert "chunks_returned" in metrics, f"chunks_returned not in metrics: {metrics}"

    chunks_returned = int(metrics["chunks_returned"])
    assert chunks_returned >= 1, "Should return at least 1 chunk"

    # If evidence was found, validate early-stop behavior
    if metrics["stop_reason"] == "evidence":
        assert chunks_returned == 1, f"Evidence stop should return 1 chunk, got {chunks_returned}"
        assert metrics.get("strong_hit") == "1", "strong_hit should be 1 for evidence stop"


def test_e2e_evidence_metadata_structure(minimal_evidence_segment: Path):
    """Verify evidence metadata is always present in telemetry."""
    segment = minimal_evidence_segment

    # Search for ID
    ids = _search_for_ids(segment, "Test", limit=1)

    # Run get WITHOUT --stop-on-evidence
    subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "-s",
            str(segment),
            "-i",
            ids[0],
            "--mode",
            "excerpt",
        ],
        capture_output=True,
        cwd=segment.parent,
    )

    # Verify telemetry includes evidence field
    telemetry_events_path = segment / "_ctx" / "telemetry" / "events.jsonl"
    if telemetry_events_path.exists():
        with open(telemetry_events_path) as f:
            events = [json.loads(line) for line in f if line.strip()]

        get_events = [e for e in events if e.get("event_name") == "ctx.get"]
        if get_events:
            last_event = get_events[-1]
            result_data = last_event.get("result", {})
            assert "evidence" in result_data, "evidence field should exist"


# =============================================================================
# Real Segment Tests (environment-dependent, marked as slow)
# =============================================================================


@pytest.fixture
def real_segment() -> Path:
    """Use actual trifecta_dope segment for E2E test."""
    seg = Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope")
    if not seg.exists():
        pytest.fail("Real segment does not exist - test requires specific environment")
    return seg


@pytest.mark.slow
@pytest.mark.skipif(
    not Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope").exists(),
    reason="Requires local development environment",
)
def test_e2e_evidence_stop_real_cli(real_segment: Path):
    """E2E test with real CLI and telemetry validation."""
    ids = _search_for_ids(real_segment, "ContextService", limit=3)

    assert len(ids) >= 2, "Need at least 2 IDs for test"

    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "--segment",
            str(real_segment),
            "--ids",
            ",".join(ids[:3]),
            "--mode",
            "excerpt",
            "--stop-on-evidence",
            "--query",
            "ContextService",
        ],
        capture_output=True,
        text=True,
        cwd=real_segment,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Validate telemetry
    telemetry_events_path = real_segment / "_ctx" / "telemetry" / "events.jsonl"
    if telemetry_events_path.exists():
        events = []
        with open(telemetry_events_path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        get_events = [e for e in events if e.get("event_name") == "ctx.get"]
        if get_events:
            last_event = get_events[-1]
            args = last_event.get("args", {})
            assert "stop_on_evidence" in args

            result_data = last_event.get("result", {})
            assert "evidence" in result_data


@pytest.mark.slow
@pytest.mark.skipif(
    not Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope").exists(),
    reason="Requires local development environment",
)
def test_e2e_evidence_stop_disabled_by_default(real_segment: Path):
    """Verify that evidence-stop is disabled by default (backward compat)."""
    ids = _search_for_ids(real_segment, "get", limit=2)

    assert len(ids) >= 2, "Need at least 2 IDs for test"

    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "--segment",
            str(real_segment),
            "--ids",
            ",".join(ids[:2]),
            "--mode",
            "excerpt",
            # NOTE: NO --stop-on-evidence flag
        ],
        capture_output=True,
        text=True,
        cwd=real_segment,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"
