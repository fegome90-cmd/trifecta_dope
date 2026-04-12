"""Tests for SkillManifest domain model.

TDD Phase 2: RED - These tests should FAIL until implementation exists.

Contract:
- Schema v2: id, name, relative_path, description, source are required
- Fail-closed: Invalid entries cause error, not silent skip
- Identity: skill_id is stable, chunk_id is derived

Author: Trifecta Team
Date: 2026-03-19
"""

import json
from pathlib import Path


from src.domain.result import Err, Ok


class TestSkillManifestLoading:
    """Tests for manifest loading and validation."""

    def test_load_valid_manifest_v2(self, tmp_path: Path) -> None:
        """
        RED TEST: Load a valid schema_version 2 manifest.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:test-skill",
                    "name": "test-skill",
                    "relative_path": "test-skill.md",
                    "description": "A test skill",
                    "source": "test-source",
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest_data))

        # Create the referenced file
        (tmp_path / "test-skill.md").write_text("# Test Skill\nTest content")

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Ok)
        manifest = result.value
        assert manifest.schema_version == 2
        assert len(manifest.skills) == 1
        assert manifest.skills[0].id == "skill:test-skill"

    def test_load_fails_when_missing_required_field(self, tmp_path: Path) -> None:
        """
        RED TEST: Manifest missing required field should return Err.
        Fail-closed: no silent skipping.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:test-skill",
                    "name": "test-skill",
                    # missing: relative_path, description, source
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest_data))

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Err)
        errors = result.error
        assert any("relative_path" in str(e).lower() for e in errors)

    def test_load_fails_when_file_not_exists(self, tmp_path: Path) -> None:
        """
        RED TEST: Missing manifest file should return Err.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "nonexistent.json"

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Err)
        assert "not found" in str(result.error).lower()

    def test_load_fails_when_invalid_json(self, tmp_path: Path) -> None:
        """
        RED TEST: Corrupt JSON should return Err with diagnostic.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_path.write_text("{ invalid json }")

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Err)
        assert "parse" in str(result.error).lower() or "json" in str(result.error).lower()

    def test_load_fails_when_relative_path_not_exists(self, tmp_path: Path) -> None:
        """
        RED TEST: Entry referencing non-existent file should return Err.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:missing-skill",
                    "name": "missing-skill",
                    "relative_path": "nonexistent.md",  # This file doesn't exist
                    "description": "A missing skill",
                    "source": "test-source",
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest_data))

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Err)
        errors = result.error
        assert any("nonexistent" in str(e) or "not found" in str(e).lower() for e in errors)


class TestSkillManifestEntryIdentity:
    """Tests for skill_id vs chunk_id distinction."""

    def test_skill_id_is_stable(self, tmp_path: Path) -> None:
        """
        RED TEST: skill_id should be stable across builds.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:stable-id",
                    "name": "stable-skill",
                    "relative_path": "stable.md",
                    "description": "Stable skill",
                    "source": "test",
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest_data))

        # Create the file
        (tmp_path / "stable.md").write_text("# Test content")

        result1 = SkillManifest.load(manifest_path, segment_path=tmp_path)
        result2 = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result1, Ok) and isinstance(result2, Ok)
        assert result1.value.skills[0].skill_id == result2.value.skills[0].skill_id
        assert result1.value.skills[0].skill_id == "skill:stable-id"

    def test_chunk_id_includes_content_hash(self, tmp_path: Path) -> None:
        """
        RED TEST: chunk_id should include hash of content.
        chunk_id changes when content changes, skill_id doesn't.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:content-skill",
                    "name": "content-skill",
                    "relative_path": "content.md",
                    "description": "Content skill",
                    "source": "test",
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest_data))

        skill_file = tmp_path / "content.md"

        # First version
        skill_file.write_text("Version 1")
        result1 = SkillManifest.load(manifest_path, segment_path=tmp_path)
        assert isinstance(result1, Ok)
        chunk_id_1 = result1.value.skills[0].chunk_id

        # Second version (content changed)
        skill_file.write_text("Version 2 with different content")
        result2 = SkillManifest.load(manifest_path, segment_path=tmp_path)
        assert isinstance(result2, Ok)
        chunk_id_2 = result2.value.skills[0].chunk_id

        # skill_id should be same
        assert result1.value.skills[0].skill_id == result2.value.skills[0].skill_id

        # chunk_id should be different (content changed)
        assert chunk_id_1 != chunk_id_2


class TestSkillManifestFindSkill:
    """Tests for finding skills by path or name."""

    def test_find_by_relative_path(self, tmp_path: Path) -> None:
        """
        RED TEST: Find skill by relative path.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:findable",
                    "name": "findable-skill",
                    "relative_path": "findable.md",
                    "description": "Findable skill",
                    "source": "test",
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest_data))
        (tmp_path / "findable.md").write_text("# Content")

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)
        assert isinstance(result, Ok)

        skill = result.value.find_by_relative_path("findable.md")
        assert skill is not None
        assert skill.name == "findable-skill"

    def test_find_by_relative_path_not_found(self, tmp_path: Path) -> None:
        """
        RED TEST: Find skill by path returns None if not in manifest.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"
        manifest_data = {
            "schema_version": 2,
            "skills": []
        }
        manifest_path.write_text(json.dumps(manifest_data))

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)
        assert isinstance(result, Ok)

        skill = result.value.find_by_relative_path("nonexistent.md")
        assert skill is None


class TestSkillManifestMigration:
    """Tests for v1 to v2 migration."""

    def test_migration_v1_to_v2_success(self, tmp_path: Path) -> None:
        """
        RED TEST: Migrate valid v1 manifest to v2.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"

        # v1 manifest (with source_path)
        v1_data = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "test-skill",
                    "source_path": "/some/path/test-skill/SKILL.md",
                    "description": "Test skill",
                    "source": "test-source",
                }
            ]
        }
        manifest_path.write_text(json.dumps(v1_data))

        # Create the expected file
        (tmp_path / "test-skill.md").write_text("# Test skill content")

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Ok)
        manifest = result.value
        assert manifest.schema_version == 2
        assert len(manifest.skills) == 1
        assert manifest.skills[0].relative_path == "test-skill.md"
        assert manifest.skills[0].id == "skill:test-skill"

    def test_migration_v1_rejects_ambiguous_path(self, tmp_path: Path) -> None:
        """
        RED TEST: v1 migration rejects paths not ending in /SKILL.md.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"

        v1_data = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "bad-skill",
                    "source_path": "/some/path/bad-skill.md",  # Not /SKILL.md
                    "description": "Bad skill",
                    "source": "test",
                }
            ]
        }
        manifest_path.write_text(json.dumps(v1_data))

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Err)
        errors = result.error
        assert any("SKILL.md" in str(e) for e in errors)

    def test_migration_v1_rejects_missing_file(self, tmp_path: Path) -> None:
        """
        RED TEST: v1 migration rejects if derived file doesn't exist.
        """
        from src.domain.skill_manifest import SkillManifest

        manifest_path = tmp_path / "skills_manifest.json"

        v1_data = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "missing-skill",
                    "source_path": "/some/path/missing-skill/SKILL.md",
                    "description": "Missing skill",
                    "source": "test",
                }
            ]
        }
        manifest_path.write_text(json.dumps(v1_data))

        # Note: NOT creating the file

        result = SkillManifest.load(manifest_path, segment_path=tmp_path)

        assert isinstance(result, Err)
        errors = result.error
        assert any("not found" in str(e).lower() or "missing" in str(e).lower() for e in errors)
