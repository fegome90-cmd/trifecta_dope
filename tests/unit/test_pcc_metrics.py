from pathlib import Path

from src.application.pcc_metrics import parse_feature_map


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
