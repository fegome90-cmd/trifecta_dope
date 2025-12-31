from pathlib import Path

from src.application.pcc_metrics import parse_feature_map, evaluate_pcc


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
