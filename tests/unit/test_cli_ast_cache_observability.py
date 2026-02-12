from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def _create_min_segment(segment: Path) -> None:
    segment.mkdir(parents=True, exist_ok=True)
    (segment / "foo.py").write_text("def foo() -> int:\n    return 1\n")


def test_cache_stats_uses_segment_root_not_cwd(tmp_path: Path, monkeypatch) -> None:
    segment = tmp_path / "seg_a"
    other_cwd = tmp_path / "other_cwd"
    other_cwd.mkdir()
    _create_min_segment(segment)

    # Generate persistent cache entry
    first = runner.invoke(
        app,
        [
            "ast",
            "symbols",
            "sym://python/mod/foo",
            "--segment",
            str(segment),
            "--persist-cache",
        ],
    )
    assert first.exit_code == 0, first.stdout

    # Query stats from a different cwd: must still resolve segment cache
    monkeypatch.chdir(other_cwd)
    stats = runner.invoke(app, ["ast", "cache-stats", "--segment", str(segment)])
    assert stats.exit_code == 0, stats.stdout

    payload = json.loads(stats.stdout)
    assert payload["status"] == "ok"
    assert "stats" in payload, payload
    assert payload["stats"]["entries"] >= 1, payload


def test_ast_symbols_reports_miss_reason(tmp_path: Path) -> None:
    segment = tmp_path / "seg_b"
    _create_min_segment(segment)

    out = runner.invoke(
        app,
        [
            "ast",
            "symbols",
            "sym://python/mod/foo",
            "--segment",
            str(segment),
            "--persist-cache",
        ],
    )
    assert out.exit_code == 0, out.stdout
    payload = json.loads(out.stdout)
    assert payload["cache_status"] in {"miss", "hit"}
    assert "miss_reason" in payload, payload
