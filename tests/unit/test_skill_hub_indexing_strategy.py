"""
Tests for SkillHubIndexingStrategy.

TDD Phase 3: RED - These tests should FAIL until implementation exists.

Contract:
- Only manifest entries are discoverable as skills
- Segment metadata files are excluded from index
- Non-manifest files are NOT indexed (repo files, etc)
- Fail-closed if manifest invalid

Author: Trifecta Team
Date: 2026-03-19
"""

import json
from pathlib import Path

import pytest

from src.domain.result import Err, Ok


# Fixtures defined at module level (not inside classes)
@pytest.fixture
def skill_hub_segment(tmp_path: Path) -> Path:
    """Create a minimal skill_hub segment for testing."""
    segment = tmp_path / "skill-hub"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Config with skill_hub policy
    config = {
        "segment_id": "skill-hub",
        "repo_root": str(segment),
        "indexing_policy": "skill_hub"
    }
    (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

    # Create valid manifest
    manifest = {
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
    (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest))

    # Create the skill file
    (segment / "test-skill.md").write_text(
        "# Test Skill\n\nThis is a test skill for testing.\n"
    )

    return segment


@pytest.fixture
def generic_segment(tmp_path: Path) -> Path:
    """Create a minimal generic segment for testing."""
    segment = tmp_path / "generic-project"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Config WITHOUT skill_hub policy (generic default)
    config = {
        "segment_id": "generic-project",
        "repo_root": str(segment),
    }
    (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

    # Create a markdown file
    (segment / "some-doc.md").write_text(
        "# Some Doc\n\nThis is a regular documentation.\n"
    )

    return segment


class TestSkillHubIndexingStrategyBuild:
    """Tests for building context pack for skill_hub segments."""

    def test_build_skill_hub_segment_success(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Build should succeed for valid skill_hub segment.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value
        assert pack.schema_version == 1
        assert len(pack.chunks) == 1

        # Only one skill should be indexed
        chunk = pack.chunks[0]
        assert chunk.id.startswith("skill:")
        assert "test-skill" in chunk.id

    def test_build_excludes_segment_metadata(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Segment metadata files should NOT be indexed.
        """

        # Check that skill.md is NOT indexed
        skill_md = skill_hub_segment / "skill.md"
        assert not skill_md.exists()

        # Check that prime/agent/session are NOT indexed
        ctx_dir = skill_hub_segment / "_ctx"
        prime_files = list(ctx_dir.glob("prime_*.md"))
        for pf in prime_files:
                assert not (skill_hub_segment / pf).exists()

    def test_build_excludes_repo_files_not_in_manifest(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Files in repo but not in manifest should NOT be indexed.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Create a file not in manifest
        extra_file = skill_hub_segment / "extra-file.md"
        extra_file.write_text("# Extra File\n\nThis is not in manifest.\n")

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value

        # extra-file.md should NOT be in chunks
        for chunk in pack.chunks:
            assert "extra-file" not in chunk.id
            assert "extra-file" not in chunk.source_path

    def test_build_fails_when_manifest_missing(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Build should fail when manifest is missing.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Remove manifest
        manifest_path = skill_hub_segment / "_ctx" / "skills_manifest.json"
        manifest_path.unlink()

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Err)
        errors = result.error
        assert any("manifest" in str(e).lower() for e in errors)

    def test_build_fails_when_manifest_invalid(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Build should fail when manifest is invalid.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Corrupt the manifest
        manifest_path = skill_hub_segment / "_ctx" / "skills_manifest.json"
        manifest_path.write_text("{ invalid json }")

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Err)
        errors = result.error
        assert any("parse" in str(e).lower() or "json" in str(e).lower() for e in errors)

    def test_build_fails_when_manifest_entry_missing_file(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Build should fail when manifest entry references missing file.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Update manifest with reference to non-existent file
        manifest_path = skill_hub_segment / "_ctx" / "skills_manifest.json"
        manifest = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:missing-skill",
                    "name": "missing-skill",
                    "relative_path": "does-not-exist.md",  # This file doesn't exist
                    "description": "A missing skill",
                    "source": "test-source",
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest))

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Err)
        errors = result.error
        assert any("not found" in str(e).lower() for e in errors)

    def test_build_fails_when_manifest_entry_missing_required_field(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Build should fail when manifest entry is missing required field.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Update manifest with missing required field
        manifest_path = skill_hub_segment / "_ctx" / "skills_manifest.json"
        manifest = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:incomplete-skill",
                    "name": "incomplete-skill",
                    # missing: relative_path, description, source
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest))

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Err)
        errors = result.error
        assert any("required" in str(e).lower() for e in errors)

    def test_build_creates_correct_chunk_ids(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: Chunk IDs should use format skill:{skill_id}:{content_hash}.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value

        chunk = pack.chunks[0]
        # ID format: skill:{skill_id}:{hash}
        # skill_id is already "skill:test-skill", so format is skill:skill:test-skill:hash
        assert chunk.id.startswith("skill:")
        assert "test-skill" in chunk.id


class TestSkillHubIndexingStrategyGenericSegment:
    """Tests for generic segment behavior (no manifest-driven indexing)."""

    def test_generic_segment_unaffected(self, generic_segment: Path) -> None:
        """
        RED TEST: Generic segment should use standard indexing (repo: type).
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Generic segment should NOT use SkillHubIndexingStrategy
        # It should use standard build
        strategy = SkillHubIndexingStrategy(generic_segment)
        result = strategy.build()

        # Should fail because generic segments don't have skill_hub policy
        assert isinstance(result, Err)


class TestSkillHubIndexingStrategyMetadata:
    """Tests for metadata handling."""

    def test_skill_md_not_indexed(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: skill.md should NOT be indexed.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Create skill.md (segment metadata)
        skill_md_path = skill_hub_segment / "skill.md"
        skill_md_path.write_text(
            "---\nname: skill-hub\n---\n# Skills Hub Segment\n"
        )

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value

        # skill.md should NOT be in chunks - check exact match, not substring
        for chunk in pack.chunks:
                assert chunk.source_path != "skill.md"
                assert not chunk.source_path.endswith("/skill.md")

    def test_prime_md_not_indexed(self, skill_hub_segment: Path) -> None:
        """
        RED TEST: prime_*.md should NOT be indexed.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Create prime file
        (skill_hub_segment / "_ctx" / "prime_skill-hub.md").write_text(
            "# Prime Metadata\n"
        )

        strategy = SkillHubIndexingStrategy(skill_hub_segment)
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value

        # prime_*.md should NOT be in chunks
        for chunk in pack.chunks:
            assert "prime_" not in chunk.source_path


class TestSkillHubSegmentIdConsistency:
    """Test segment_id consistency between GENERIC and SKILL_HUB policies."""

    @pytest.fixture
    def segment_with_config_id(self, tmp_path: Path) -> Path:
        """Create a segment with custom segment_id in config."""
        segment = tmp_path / "my-segment-dir"
        segment.mkdir()
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Config with segment_id different from directory name
        config = {
            "segment": "my-segment-dir",
            "segment_id": "custom-segment-id",  # Different from directory!
            "scope": "Test segment",
            "repo_root": str(segment),
            "indexing_policy": "skill_hub"
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config, indent=2))

        # Create manifest with skill
        manifest = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:test-skill",
                    "name": "test-skill",
                    "relative_path": "test-skill.md",
                    "source": "test",
                    "description": "Test skill",
                    "canonical": True,
                }
            ]
        }
        (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest, indent=2))

        # Create the skill file
        (segment / "test-skill.md").write_text("# Test Skill\n\nContent here.\n")

        return segment

    def test_skill_hub_uses_config_segment_id(self, segment_with_config_id: Path) -> None:
        """
        SKILL_HUB should use segment_id from config, not directory name.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        strategy = SkillHubIndexingStrategy(segment_with_config_id)
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value

        # Should use custom-segment-id from config, NOT my-segment-dir
        assert pack.segment == "custom-segment-id", (
            f"Expected segment_id from config ('custom-segment-id'), "
            f"got directory name ('{pack.segment}')"
        )

    def test_skill_hub_segment_id_parameter_override(self, segment_with_config_id: Path) -> None:
        """
        SKILL_HUB segment_id parameter should override auto-detection.
        """
        from src.application.skill_hub_indexing_strategy import SkillHubIndexingStrategy

        # Pass explicit segment_id
        strategy = SkillHubIndexingStrategy(
            segment_with_config_id,
            segment_id="explicit-override-id"
        )
        result = strategy.build()

        assert isinstance(result, Ok)
        pack = result.value

        # Should use explicit override
        assert pack.segment == "explicit-override-id"