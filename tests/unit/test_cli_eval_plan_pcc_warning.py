"""
Tests for eval-plan PCC warning when feature_map parsing fails.
TDD Phase: RED -> GREEN
"""

from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def test_eval_plan_warns_on_feature_map_parse_error(tmp_path: Path) -> None:
    segment = tmp_path / "segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)

    # Malformed feature_map table (missing header)
    prime_path = ctx_dir / "prime_segment.md"
    prime_path.write_text(
        """
### index.feature_map
|---------|-----------|-------|----------|
| telemetry | `skill:*` | `src/infrastructure/telemetry.py` | telemetry |
"""
    )

    dataset_path = tmp_path / "dataset.md"
    dataset_path.write_text('1. "do thing" | fallback | note\n')

    result = runner.invoke(
        app,
        [
            "ctx",
            "eval-plan",
            "--segment",
            str(segment),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "PCC Metrics: Failed to parse feature_map" in result.stdout
