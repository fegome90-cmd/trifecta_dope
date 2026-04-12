"""Phase D consumer cutover tests for skill_hub change."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.infrastructure.aliases_fs import load_skills_manifest


def test_aliases_fs_reads_only_canonical_manifest_contract(tmp_path: Path) -> None:
    manifest_path = tmp_path / "_ctx" / "skills_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "skills": [
                    {
                        "id": "skill:a",
                        "name": "a",
                        "relative_path": "a.md",
                        "description": "Skill A",
                        "source": "test",
                        "canonical": True,
                    },
                    {
                        "id": "skill:b",
                        "name": "b",
                        "relative_path": "b.md",
                        "description": "Skill B",
                        "source": "test",
                        "canonical": False,
                    },
                ],
            }
        )
    )

    skills = load_skills_manifest(tmp_path)

    assert skills == [
        {
            "name": "a",
            "source_path": "a.md",
            "description": "Skill A",
        }
    ]


def test_aliases_fs_rejects_legacy_source_path_manifest_shape(tmp_path: Path) -> None:
    manifest_path = tmp_path / "_ctx" / "skills_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "skills": [
                    {
                        "name": "legacy",
                        "source_path": "/tmp/legacy/SKILL.md",
                        "description": "legacy",
                    }
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="canonical manifest contract"):
        load_skills_manifest(tmp_path)
