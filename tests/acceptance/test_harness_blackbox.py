"""Smoke tests for black-box CLI harness."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from harness_blackbox import (
    run_command_with_extraction,
    parse_pd_report,
    extract_error_card,
    generate_error_prompt,
)


def test_harness_extracts_pd_report():
    """Verify harness extracts PD_REPORT from CLI output."""
    # Run a command with --pd-report
    result = run_command_with_extraction(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "get",
            "-s",
            ".",
            "--ids",
            "prime:363a719791",
            "--pd-report",
        ],
        cwd="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
    )

    # Should succeed
    assert result["success"] is True, f"Command should succeed, got: {result}"

    # Should extract PD_REPORT
    assert "pd_report" in result, "Should extract PD_REPORT"
    pd_report = result["pd_report"]

    # Verify invariant keys
    assert "v" in pd_report
    assert pd_report["v"] == "1"
    assert "stop_reason" in pd_report
    assert "chunks_returned" in pd_report
    assert "chunks_requested" in pd_report
    assert "chars_returned_total" in pd_report
    assert "strong_hit" in pd_report
    assert "support" in pd_report


def test_parse_pd_report_order_independent():
    """Verify PD_REPORT parser is order-independent."""
    # Test with different order
    line1 = "PD_REPORT v=1 stop_reason=complete chunks_returned=1"
    line2 = "PD_REPORT chunks_returned=1 v=1 stop_reason=complete"

    result1 = parse_pd_report(line1)
    result2 = parse_pd_report(line2)

    assert result1["v"] == "1"
    assert result1["stop_reason"] == "complete"
    assert result1["chunks_returned"] == 1  # Now int, not str

    # Same keys extracted regardless of order
    assert set(result1.keys()) == set(result2.keys())


def test_error_card_extraction():
    """Verify Error Card extraction from stderr."""
    stderr = """
❌ TRIFECTA_ERROR

TRIFECTA_ERROR_CODE: SEGMENT_NOT_INITIALIZED
CLASS: Precondition
CAUSE: Segment directory exists but is not initialized

NEXT STEPS:
1. Run trifecta create
"""

    error_card = extract_error_card(stderr)

    assert error_card is not None
    assert error_card["code"] == "SEGMENT_NOT_INITIALIZED"
    assert error_card["class"] == "Precondition"
    assert "not initialized" in error_card["cause"]


def test_error_prompt_generation():
    """Verify Error→Prompt generation is deterministic."""
    cmd = ["uv", "run", "trifecta", "ctx", "sync", "-s", "/tmp/test"]
    returncode = 1
    error_card = {
        "code": "SEGMENT_NOT_INITIALIZED",
        "class": "Precondition",
        "cause": "Missing trifecta_config.json",
    }

    prompt = generate_error_prompt(cmd, returncode, error_card)

    # Verify structure
    assert "❌ Command Failed" in prompt
    assert "Exit Code: 1" in prompt
    assert "SEGMENT_NOT_INITIALIZED" in prompt
    assert "Recovery Steps:" in prompt
    assert "1. Run: trifecta create" in prompt
    assert "2." in prompt
    assert "3." in prompt


def test_harness_handles_failure():
    """Verify harness captures failure info (without actual failure)."""
    # Simulate a failure scenario by checking structure
    stderr_sample = "ERROR: Something went wrong"

    # If no Error Card, should have fallback error_info
    error_card = extract_error_card(stderr_sample)
    assert error_card is None  # No proper Error Card in this stderr

    # Harness would add error_info in this case (tested via integration)


def test_pd_report_typed_fields():
    """Verify PD_REPORT numeric fields are parsed as int."""
    line = "PD_REPORT v=1 stop_reason=complete chunks_returned=2 chunks_requested=3 chars_returned_total=1024 strong_hit=1 support=0"

    result = parse_pd_report(line)

    # Numeric fields should be int
    assert isinstance(result["chunks_returned"], int)
    assert result["chunks_returned"] == 2

    assert isinstance(result["chunks_requested"], int)
    assert result["chunks_requested"] == 3

    assert isinstance(result["chars_returned_total"], int)
    assert result["chars_returned_total"] == 1024

    assert isinstance(result["strong_hit"], int)
    assert result["strong_hit"] == 1

    assert isinstance(result["support"], int)
    assert result["support"] == 0

    # String fields should remain str
    assert isinstance(result["v"], str)
    assert result["v"] == "1"

    assert isinstance(result["stop_reason"], str)
    assert result["stop_reason"] == "complete"


def test_resolve_ids_from_existing_pack(tmp_path):
    """Verify resolve_ids extracts IDs from existing context pack."""
    # Create minimal context pack
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    pack = {
        "chunks": [
            {"id": "prime:test123", "text": "foo"},
            {"id": "skill:abc456", "text": "bar"},
            {"id": "agent:xyz789", "text": "baz"},
        ]
    }

    pack_file = ctx_dir / "context_pack.json"
    with open(pack_file, "w") as f:
        json.dump(pack, f)

    # Resolve IDs
    from scripts.harness_blackbox import resolve_ids

    ids = resolve_ids(str(tmp_path))

    # Should return first 2 IDs
    assert len(ids) == 2
    assert ids[0] == "prime:test123"
    assert ids[1] == "skill:abc456"


def test_build_ids_args_canonical():
    """Verify build_ids_args returns canonical format."""
    from scripts.harness_blackbox import build_ids_args

    # Test canonical format: comma-separated string
    result = build_ids_args(["prime:abc", "skill:xyz"])

    # Canonical: ["--ids", "id1,id2"]
    assert result == ["--ids", "prime:abc,skill:xyz"]

    # Empty list edge case
    assert build_ids_args([]) == []


def test_resolve_ids_deterministic_order(tmp_path):
    """Verify IDs are sorted by kind priority deterministically."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    # Create pack with random order (agent, skill, prime, doc)
    pack = {
        "chunks": [
            {"id": "agent:xyz", "text": "a"},
            {"id": "skill:bbb", "text": "b"},
            {"id": "prime:aaa", "text": "c"},
            {"id": "doc:ccc", "text": "d"},
            {"id": "skill:aaa", "text": "e"},
        ]
    }

    pack_file = ctx_dir / "context_pack.json"
    with open(pack_file, "w") as f:
        json.dump(pack, f)

    # Resolve IDs
    from scripts.harness_blackbox import resolve_ids

    ids = resolve_ids(str(tmp_path))

    # Should return first 2 by priority (prime=0, skill=1)
    # Within same priority, alphabetical order (skill:aaa < skill:bbb)
    assert len(ids) == 2
    assert ids[0] == "prime:aaa"  # priority 0
    assert ids[1] == "skill:aaa"  # priority 1, alphabetically first


def test_harness_no_ids_emits_error_card(tmp_path, monkeypatch, capsys):
    """Verify harness emits error card when no IDs available."""
    # Monkeypatch resolve_ids to return None
    from scripts import harness_blackbox

    monkeypatch.setattr(harness_blackbox, "resolve_ids", lambda _: None)

    # Monkeypatch sys.exit to raise exception instead
    exit_code = None

    def mock_exit(code):
        nonlocal exit_code
        exit_code = code
        raise SystemExit(code)

    monkeypatch.setattr("sys.exit", mock_exit)

    # Run main with tmp segment
    import sys

    monkeypatch.setattr(sys, "argv", ["harness", str(tmp_path)])

    # Should exit with code 2
    try:
        harness_blackbox.main()
    except SystemExit:
        pass

    assert exit_code == 2

    # Verify JSONL was written with error_card
    jsonl_file = tmp_path / "_ctx" / "telemetry" / "harness_results.jsonl"
    assert jsonl_file.exists()

    with open(jsonl_file) as f:
        entry = json.loads(f.read())

    assert entry["success"] is False
    assert entry["returncode"] == 2
    assert "error_card" in entry
    assert entry["error_card"]["code"] == "HARNESS_NO_IDS"
    assert entry["error_card"]["class"] == "Precondition"
    assert "error_prompt" in entry

    # Verify error card was printed to stdout
    captured = capsys.readouterr()
    assert "❌ Harness Failed: ID Resolution" in captured.out
    assert "HARNESS_NO_IDS" in captured.out
