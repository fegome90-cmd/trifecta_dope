from pathlib import Path

import pytest

from src.application.pcc_metrics import parse_feature_map, evaluate_pcc, summarize_pcc


def test_parse_feature_map_paths(tmp_path: Path) -> None:
    prime = tmp_path / "prime_test.md"
    prime.write_text(
        """
### index.feature_map
| Feature | Chunk IDs | Paths | Keywords |
|---------|-----------|-------|----------|
| telemetry | `skill:*` | `README.md`, `src/infrastructure/telemetry.py` | telemetry |
| context_pack | `skill:*` | `src/application/use_cases.py` | context pack |
"""
    )

    feature_map = parse_feature_map(prime)

    assert feature_map["telemetry"] == ["README.md", "src/infrastructure/telemetry.py"]
    assert feature_map["context_pack"] == ["src/application/use_cases.py"]


def test_parse_feature_map_feature_in_name(tmp_path: Path) -> None:
    """Feature names can contain 'Feature' string without being filtered out."""
    prime = tmp_path / "prime_test.md"
    prime.write_text(
        """
### index.feature_map
| Feature | Chunk IDs | Paths | Keywords |
|---------|-----------|-------|----------|
| FeatureFlag | `skill:*` | `src/feature_flag.py` | feature flag |
| telemetry | `skill:*` | `src/telemetry.py` | telemetry |
"""
    )

    feature_map = parse_feature_map(prime)

    assert "FeatureFlag" in feature_map
    assert feature_map["FeatureFlag"] == ["src/feature_flag.py"]
    assert feature_map["telemetry"] == ["src/telemetry.py"]


def test_parse_feature_map_malformed_no_header(tmp_path: Path) -> None:
    """Raises ValueError when table header is missing."""
    prime = tmp_path / "prime_test.md"
    prime.write_text(
        """
### index.feature_map
| telemetry | `skill:*` | `src/telemetry.py` | telemetry |
"""
    )

    with pytest.raises(ValueError, match="header row not found"):
        parse_feature_map(prime)


def test_evaluate_pcc_path_correctness() -> None:
    feature_map = {"telemetry": ["src/infrastructure/telemetry.py"]}

    result = evaluate_pcc(
        expected_feature="telemetry",
        predicted_feature="telemetry",
        predicted_paths=["src/infrastructure/telemetry.py"],
        feature_map=feature_map,
        selected_by="nl_trigger",
    )

    assert result["path_correct"] is True
    assert result["false_fallback"] is False
    assert result["safe_fallback"] is False


def test_evaluate_pcc_path_incorrect() -> None:
    """Path incorrect when predicted path not in expected paths."""
    feature_map = {"telemetry": ["src/infrastructure/telemetry.py"]}

    result = evaluate_pcc(
        expected_feature="telemetry",
        predicted_feature="telemetry",
        predicted_paths=["src/other.py"],  # Wrong path
        feature_map=feature_map,
        selected_by="nl_trigger",
    )

    assert result["path_correct"] is False
    assert result["false_fallback"] is False
    assert result["safe_fallback"] is False


def test_evaluate_pcc_false_fallback() -> None:
    """False fallback when expected feature != fallback but selected_by == fallback."""
    result = evaluate_pcc(
        expected_feature="telemetry",
        predicted_feature=None,
        predicted_paths=[],
        feature_map={},
        selected_by="fallback",
    )

    assert result["path_correct"] is False
    assert result["false_fallback"] is True
    assert result["safe_fallback"] is False


def test_evaluate_pcc_safe_fallback() -> None:
    """Safe fallback when expected feature == fallback and selected_by == fallback."""
    result = evaluate_pcc(
        expected_feature="fallback",
        predicted_feature=None,
        predicted_paths=[],
        feature_map={},
        selected_by="fallback",
    )

    assert result["path_correct"] is False
    assert result["false_fallback"] is False
    assert result["safe_fallback"] is True


def test_summarize_pcc_counts() -> None:
    rows = [
        {"path_correct": True, "false_fallback": False, "safe_fallback": False},
        {"path_correct": False, "false_fallback": True, "safe_fallback": False},
    ]

    summary = summarize_pcc(rows)
    assert summary["path_correct_count"] == 1
    assert summary["false_fallback_count"] == 1
    assert summary["safe_fallback_count"] == 0


def test_summarize_pcc_empty_rows() -> None:
    """Handles empty input gracefully."""
    summary = summarize_pcc([])
    assert summary["path_correct_count"] == 0
    assert summary["false_fallback_count"] == 0
    assert summary["safe_fallback_count"] == 0
