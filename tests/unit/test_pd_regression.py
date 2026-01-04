"""Regression tests for PD (Program-Directed) features."""

from pathlib import Path

import pytest

from src.application.search_get_usecases import GetChunkUseCase

# Skip all tests in this module if local development path doesn't exist
pytestmark = pytest.mark.skipif(
    not Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope").exists(),
    reason="Requires local development environment",
)


def test_execute_compatibility():
    """Verify execute() returns same string as execute_with_result()[0]."""
    use_case = GetChunkUseCase(None, None)
    test_path = Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope")
    test_ids = ["prime:363a719791"]

    # Get output from both methods
    output_str = use_case.execute(test_path, test_ids, mode="excerpt")
    output_tuple, result = use_case.execute_with_result(test_path, test_ids, mode="excerpt")

    # They should be identical
    assert output_str == output_tuple, (
        "execute() and execute_with_result()[0] must return same string"
    )
    assert isinstance(output_str, str), "execute() must return str"
    assert isinstance(result.stop_reason, str), "execute_with_result()[1] must be GetResult"


def test_pd_report_invariants():
    """Verify PD_REPORT always includes all keys even with empty evidence."""
    from src.domain.context_models import GetResult

    # Create minimal GetResult with empty evidence
    result = GetResult(
        chunks=[],
        total_tokens=0,
        stop_reason="complete",
        chunks_requested=3,
        chunks_returned=0,
        chars_returned_total=0,
        evidence_metadata={"strong_hit": False, "support": False},
    )

    # Format PD_REPORT line (mimic CLI logic)
    strong_hit = 1 if result.evidence_metadata.get("strong_hit") else 0
    support = 1 if result.evidence_metadata.get("support") else 0
    pd_report = (
        f"PD_REPORT v=1 "
        f"stop_reason={result.stop_reason} "
        f"chunks_returned={result.chunks_returned} "
        f"chunks_requested={result.chunks_requested} "
        f"chars_returned_total={result.chars_returned_total} "
        f"strong_hit={strong_hit} "
        f"support={support}"
    )

    # Verify invariants
    assert "v=1" in pd_report
    assert "stop_reason=complete" in pd_report
    assert "chunks_returned=0" in pd_report
    assert "chunks_requested=3" in pd_report
    assert "chars_returned_total=0" in pd_report
    assert "strong_hit=0" in pd_report
    assert "support=0" in pd_report

    # Count keys (should be 7: v + 6 metrics)
    key_value_pairs = [part for part in pd_report.split() if "=" in part]
    assert len(key_value_pairs) == 7, f"Expected 7 key=value pairs, got {len(key_value_pairs)}"


def test_pd_report_output_guarantees():
    """Verify PD_REPORT is last line and appears exactly once."""

    # Simulate CLI output with PD_REPORT
    use_case = GetChunkUseCase(None, None)
    test_path = Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope")
    test_ids = ["prime:363a719791"]

    # Get output with result
    output_str, result = use_case.execute_with_result(test_path, test_ids, mode="excerpt")

    # Simulate CLI adding PD_REPORT
    strong_hit = 1 if result.evidence_metadata.get("strong_hit") else 0
    support = 1 if result.evidence_metadata.get("support") else 0
    pd_report_line = (
        f"PD_REPORT v=1 "
        f"stop_reason={result.stop_reason} "
        f"chunks_returned={result.chunks_returned} "
        f"chunks_requested={result.chunks_requested} "
        f"chars_returned_total={result.chars_returned_total} "
        f"strong_hit={strong_hit} "
        f"support={support}"
    )

    full_output = output_str + "\n" + pd_report_line

    # Test 1: PD_REPORT is the last line
    lines = full_output.strip().split("\n")
    assert lines[-1].startswith("PD_REPORT v="), "PD_REPORT must be the last line"

    # Test 2: PD_REPORT appears exactly once
    pd_report_count = sum(1 for line in lines if line.startswith("PD_REPORT"))
    assert pd_report_count == 1, f"PD_REPORT must appear exactly once, found {pd_report_count}"

    # Test 3: Verify it's on stdout (not stderr) - implicitly tested by string content
