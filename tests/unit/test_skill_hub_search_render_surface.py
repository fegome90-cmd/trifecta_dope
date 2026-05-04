import json
from unittest.mock import MagicMock

from src.application.search_get_usecases import SearchUseCase


def test_skill_hub_plain_preview_uses_human_description_not_managed_artifacts(tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    managed_preview = "\n".join(
        [
            "<!-- managed-by:indexing-skills-safely:start -->",
            "read /Users/example/.claude/skills/django-security/SKILL.md",
            "# Skill: django-security",
            "**Source**: claude-skills",
            "Django security hardening patterns for auth, CSRF, headers, and safe defaults.",
            "<!-- managed-by:indexing-skills-safely:end -->",
        ]
    )
    pack = {
        "schema_version": 1,
        "segment": "skills-hub",
        "created_at": "2026-04-30T00:00:00",
        "digest": "",
        "source_files": [],
        "chunks": [
            {
                "id": "skill:django-security:abc123",
                "doc": "skill",
                "title_path": ["django-security.md"],
                "text": managed_preview,
                "char_count": len(managed_preview),
                "token_est": 50,
                "source_path": "django-security.md",
                "chunking_method": "whole_file",
            }
        ],
        "index": [
            {
                "id": "skill:django-security:abc123",
                "title_path_norm": "django-security.md",
                "preview": managed_preview,
                "token_est": 50,
            }
        ],
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack))

    output = SearchUseCase(MagicMock(), MagicMock()).execute(tmp_path, "security")

    assert "Django security hardening patterns" in output
    assert "managed-by:indexing-skills-safely" not in output
    assert "read /Users/example" not in output


def test_skill_hub_plain_search_keeps_skill_path_discoverable(tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    managed_preview = "\n".join(
        [
            "<!-- managed-by:indexing-skills-safely:start -->",
            "read /Users/example/.codex/skills/skill-hub-doctor/SKILL.md",
            "# Skill: skill-hub-doctor",
            "**Source**: codex-skills",
            "**Resolved Path**: /Users/example/.codex/skills/skill-hub-doctor/SKILL.md",
            "Use when skill-hub is broken or rendering the wrong surface.",
            "<!-- managed-by:indexing-skills-safely:end -->",
        ]
    )
    truncated_index_preview = "\n".join(
        [
            "<!-- managed-by:indexing-skills-safely:start -->",
            "read /Users/example/.codex/skills/skill-hub-doctor/SKILL.md",
            "# Skill: skill-hub-doctor",
            "**Source**: codex-skills",
            "**Resolved Path**: /Users/example/.codex/skills/skill-hub-doctor/SKILL.md",
        ]
    )
    pack = {
        "schema_version": 1,
        "segment": "skills-hub",
        "created_at": "2026-04-30T00:00:00",
        "digest": "",
        "source_files": [],
        "chunks": [
            {
                "id": "skill:skill-hub-doctor:abc123",
                "doc": "skill",
                "title_path": ["skill-hub-doctor.md"],
                "text": managed_preview,
                "char_count": len(managed_preview),
                "token_est": 50,
                "source_path": "skill-hub-doctor.md",
                "chunking_method": "whole_file",
            }
        ],
        "index": [
            {
                "id": "skill:skill-hub-doctor:abc123",
                "title_path_norm": "skill-hub-doctor.md",
                "preview": truncated_index_preview,
                "token_est": 50,
            }
        ],
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack))

    output = SearchUseCase(MagicMock(), MagicMock()).execute(tmp_path, "skill-hub doctor")

    assert "Path: /Users/example/.codex/skills/skill-hub-doctor/SKILL.md" in output
    assert "Preview: Use when skill-hub is broken" in output
    assert "Preview: **Resolved Path**" not in output
