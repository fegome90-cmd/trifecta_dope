from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_audit_skill_hub_frontmatter_script_reports_manifest_backed_failures(tmp_path: Path) -> None:
    broken_skill = tmp_path / "broken-skill" / "SKILL.md"
    broken_skill.parent.mkdir(parents=True)
    broken_skill.write_text(
        "---\nname: broken-skill\ndescription: Use when broken. Triggers on: invalid colon.\n---\n"
    )

    valid_skill = tmp_path / "valid-skill" / "SKILL.md"
    valid_skill.parent.mkdir(parents=True)
    valid_skill.write_text("---\nname: valid-skill\ndescription: valid\n---\n")

    manifest = tmp_path / "skills_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "skills": [
                    {
                        "name": "broken-skill",
                        "source": "demo",
                        "source_path": str(broken_skill),
                    },
                    {
                        "name": "valid-skill",
                        "source": "demo",
                        "source_path": str(valid_skill),
                    },
                ],
            }
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_skill_hub_frontmatter.py",
            "--manifest",
            str(manifest),
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["broken_count"] == 1
    assert payload["counts_by_error_type"] == {"ScannerError": 1}
    assert payload["failures"][0]["name"] == "broken-skill"
