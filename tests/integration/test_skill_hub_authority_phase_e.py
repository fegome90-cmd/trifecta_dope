"""Phase E integration tests (legacy writer shutdown) for skill_hub."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _ingest_script() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "ingest_trifecta.py"


def test_ingest_trifecta_rejects_skill_hub_policy_segment(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    segment = repo_root / "skills-hub"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (segment / "skill.md").write_text("# skill_hub segment\n")
    (ctx_dir / "trifecta_config.json").write_text(
        json.dumps({"segment": "skills-hub", "indexing_policy": "skill_hub"})
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_ingest_script()),
            "--segment",
            "skills-hub",
            "--repo-root",
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "ingest_trifecta.py is not allowed for skill_hub segments" in result.stderr


def test_ingest_trifecta_keeps_generic_segments_unchanged(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    segment = repo_root / "generic-segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (segment / "skill.md").write_text("# generic segment\n")
    (ctx_dir / "trifecta_config.json").write_text(
        json.dumps({"segment": "generic-segment", "indexing_policy": "generic"})
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_ingest_script()),
            "--segment",
            "generic-segment",
            "--repo-root",
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (ctx_dir / "context_pack.json").exists()


def test_ingest_trifecta_rejects_runtime_publish_from_external_manifest_input(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    segment = repo_root / "skills-hub"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True, exist_ok=True)
    (segment / "skill.md").write_text("# skill_hub segment\n")
    (ctx_dir / "trifecta_config.json").write_text(
        json.dumps({"segment": "skills-hub", "indexing_policy": "skill_hub"})
    )
    (ctx_dir / "skills_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "skills": [
                    {
                        "id": "skill:external-a",
                        "name": "external-a",
                        "relative_path": "external-a.md",
                        "description": "external staging input",
                        "source": "external_inventory",
                        "canonical": True,
                    }
                ],
            }
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_ingest_script()),
            "--segment",
            "skills-hub",
            "--repo-root",
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "ingest_trifecta.py is not allowed for skill_hub segments" in result.stderr
    assert not (ctx_dir / "context_pack.json").exists()
