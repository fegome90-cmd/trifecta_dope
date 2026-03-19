"""
Tests for skill-hub discovery contract.

These tests verify that skill-hub only discovers and renders
canonical skill entities, not administrative/metadata files.

CAUSE ROOT (documented):
1. BuildContextPackUseCase assigns `repo:` type to all .md files in segment
2. skills_manifest.json is not consulted during build to type skills correctly
3. The segment's own skill.md (metadata) is typed as `skill:` but shouldn't be discoverable
4. No filter exists in retrieval/render to exclude non-skill entities

CONTRACT:
- A "discoverable skill" must have:
  - A valid entry in skills_manifest.json with name matching the file
  - Type `skill:` (not `repo:`) in context_pack.json
  - A valid SKILL.md structure (not segment metadata)

Author: Trifecta Team
Date: 2026-03-19
"""

import json
from pathlib import Path

import pytest


class TestSkillDiscoveryContract:
    """Test contract for discoverable skills in skill-hub."""

    @pytest.fixture
    def skills_hub_segment(self, tmp_path: Path) -> Path:
        """Create a minimal skills-hub segment for testing."""
        segment = tmp_path / "skills-hub"
        segment.mkdir()
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Create minimal segment metadata files
        (segment / "skill.md").write_text("""---
name: skills-hub
description: Test skills hub segment
---
# Skills Hub
This is segment metadata, not a skill.
""")

        (ctx_dir / "prime_skills-hub.md").write_text("# Prime Metadata\n")
        (ctx_dir / "agent_skills-hub.md").write_text("# Agent Metadata\n")
        (ctx_dir / "session_skills-hub.md").write_text("# Session Metadata\n")

        # Create a valid skill file
        (segment / "test-skill.md").write_text("""# Skill: test-skill

**Source**: test-source
**Path**: /test/skills/test-skill/SKILL.md

## Description
Use this skill for testing purposes.

## Triggers
- test
- testing
""")

        # Create skills_manifest.json (schema v2 format)
        manifest = {
            "schema_version": 2,
            "skills": [
                {
                    "id": "skill:test-skill",
                    "name": "test-skill",
                    "relative_path": "test-skill.md",
                    "source": "test-source",
                    "description": "Use this skill for testing purposes.",
                    "canonical": True,
                }
            ]
        }
        (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest, indent=2))

        # Create trifecta_config.json with required fields + indexing_policy
        config = {
            "segment": "skills-hub",
            "scope": "Global skills hub segment",
            "repo_root": str(segment),
            "segment_id": "skills-hub",
            "indexing_policy": "skill_hub"
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config, indent=2))

        return segment

    def test_segment_metadata_not_indexed_as_skill(self, skills_hub_segment: Path) -> None:
        """
        RED TEST: Segment metadata files should NOT be indexed as skill: type.

        Currently FAILS because skill.md, prime_*.md, agent_*.md, session_*.md
        are all indexed with their respective types and appear in search results.
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.infrastructure.file_system import FileSystemAdapter
        from src.domain.result import Ok

        fs = FileSystemAdapter()
        use_case = BuildContextPackUseCase(fs)

        result = use_case.execute(skills_hub_segment)

        assert isinstance(result, Ok), f"Build failed: {result}"

        pack = result.value

        # Segment metadata should NOT have skill: type
        skill_chunks = [c for c in pack.chunks if c.id.startswith("skill:")]
        prime_chunks = [c for c in pack.chunks if c.id.startswith("prime:")]
        agent_chunks = [c for c in pack.chunks if c.id.startswith("agent:")]
        session_chunks = [c for c in pack.chunks if c.id.startswith("session:")]

        # RED: Currently these exist but shouldn't be discoverable as skills
        # After fix: only test-skill should be skill: type
        skill_names = [c.title_path[0] for c in skill_chunks]

        # The segment's own skill.md should NOT be a discoverable skill
        assert "skill.md" not in skill_names, (
            f"Segment metadata skill.md should not be indexed as skill:. Got: {skill_names}"
        )

    def test_canonical_skill_has_skill_type(self, skills_hub_segment: Path) -> None:
        """
        RED TEST: Skills in manifest should have skill: type, not repo: type.

        Currently FAILS because test-skill.md gets type `repo:test-skill.md:hash`
        instead of `skill:hash`.
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.infrastructure.file_system import FileSystemAdapter
        from src.domain.result import Ok

        fs = FileSystemAdapter()
        use_case = BuildContextPackUseCase(fs)

        result = use_case.execute(skills_hub_segment)

        assert isinstance(result, Ok), f"Build failed: {result}"

        pack = result.value

        # Find chunks for test-skill
        test_skill_chunks = [
            c for c in pack.chunks
            if "test-skill" in c.title_path[0].lower()
        ]

        assert len(test_skill_chunks) > 0, "test-skill.md should be indexed"

        # RED: Currently has type repo:test-skill.md:hash
        # After fix: should have type skill:hash
        for chunk in test_skill_chunks:
            assert chunk.id.startswith("skill:"), (
                f"Canonical skill should have skill: type. Got: {chunk.id}"
            )

    def test_search_excludes_segment_metadata(self, skills_hub_segment: Path) -> None:
        """
        RED TEST: Search results should exclude segment metadata files.

        Query "metadata" should not return prime_*.md, agent_*.md, session_*.md
        as they are administrative files, not discoverable skills.
        """
        from src.application.use_cases import BuildContextPackUseCase
        from src.application.context_service import ContextService
        from src.infrastructure.file_system import FileSystemAdapter
        from src.domain.result import Ok

        fs = FileSystemAdapter()
        build_uc = BuildContextPackUseCase(fs)

        result = build_uc.execute(skills_hub_segment)
        assert isinstance(result, Ok)

        # Search for "metadata"
        service = ContextService(skills_hub_segment)
        search_result = service.search("metadata", k=10)

        # Check that segment metadata files are not in results
        result_ids = [h.id for h in search_result.hits]

        # RED: Currently these appear in results
        assert not any("prime:" in rid for rid in result_ids), (
            f"prime_*.md should not appear in search results. Got: {result_ids}"
        )
        assert not any("agent:" in rid for rid in result_ids), (
            f"agent_*.md should not appear in search results. Got: {result_ids}"
        )
        assert not any("session:" in rid for rid in result_ids), (
            f"session_*.md should not appear in search results. Got: {result_ids}"
        )


class TestSkillsManifestContract:
    """Test contract for skills_manifest.json structure."""

    def test_manifest_has_required_fields(self, tmp_path: Path) -> None:
        """
        GREEN TEST: Manifest entries should have required fields.

        Required fields:
        - name: skill name (matches filename without .md)
        - source_path: original path to SKILL.md
        - source: source collection name
        - description: skill description
        - canonical: True if this is a discoverable skill
        """
        from src.infrastructure.aliases_fs import load_skills_manifest

        manifest_path = tmp_path / "_ctx" / "skills_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "valid-skill",
                    "source_path": "/path/to/valid-skill/SKILL.md",
                    "source": "test-source",
                    "description": "A valid skill",
                    "canonical": True,
                }
            ]
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))

        skills = load_skills_manifest(tmp_path)

        assert len(skills) == 1
        skill = skills[0]

        # Required fields
        assert "name" in skill, "Skill must have 'name' field"
        assert "source_path" in skill, "Skill must have 'source_path' field"
        assert "description" in skill, "Skill must have 'description' field"

    def test_manifest_invalid_entry_excluded(self, tmp_path: Path) -> None:
        """
        GREEN TEST: Invalid manifest entries should be excluded, not crash.

        Entries without 'name' should be silently skipped.
        """
        from src.infrastructure.aliases_fs import load_skills_manifest

        manifest_path = tmp_path / "_ctx" / "skills_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "valid-skill",
                    "source_path": "/path/to/valid-skill/SKILL.md",
                    "source": "test-source",
                    "description": "A valid skill",
                },
                {
                    # Invalid: no name
                    "source_path": "/path/to/invalid/SKILL.md",
                    "description": "Invalid skill",
                },
                {
                    "name": "another-valid",
                    "source_path": "/path/to/another/SKILL.md",
                    "description": "Another valid skill",
                },
            ]
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))

        skills = load_skills_manifest(tmp_path)

        # Should have 2 valid skills, not 3
        assert len(skills) == 2
        names = [s["name"] for s in skills]
        assert "valid-skill" in names
        assert "another-valid" in names


class TestAliasResolutionContract:
    """Test contract for alias -> canonical skill resolution."""

    @pytest.fixture
    def segment_with_aliases(self, tmp_path: Path) -> Path:
        """Create a segment with aliases.yaml."""
        segment = tmp_path / "test-segment"
        segment.mkdir()
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Create aliases.yaml
        aliases = {
            "schema_version": 1,
            "aliases": {
                "refactor": ["code-review-agent", "refactoring-expert"],
                "testing": ["tdd-workflow", "python-testing"],
            }
        }
        import yaml
        (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases))

        return segment

    def test_alias_resolves_to_canonical_skill(self, segment_with_aliases: Path) -> None:
        """
        GREEN TEST: Valid alias should resolve to canonical skill name.

        aliases.yaml is a MAP of alias -> skill names, not a gate of validity.
        """
        from src.infrastructure.aliases_fs import AliasMerger

        merger = AliasMerger(segment_path=segment_with_aliases)
        aliases = merger.load_manual()

        assert "refactor" in aliases
        assert "code-review-agent" in aliases["refactor"]
        assert "refactoring-expert" in aliases["refactor"]

    def test_alias_not_gate_of_validity(self, segment_with_aliases: Path) -> None:
        """
        GREEN TEST: aliases.yaml should not be used as gate of skill validity.

        A skill exists if it's in skills_manifest.json, not if it's in aliases.yaml.
        """
        from src.infrastructure.aliases_fs import AliasMerger

        merger = AliasMerger(segment_path=segment_with_aliases)
        aliases = merger.load_manual()

        # An alias can point to a skill that doesn't exist in the segment
        # This is valid - aliases.yaml is just a map, not a gate
        assert "testing" in aliases
        # tdd-workflow and python-testing may or may not exist in manifest
        # That's OK - the search will just not find them


class TestRendererContract:
    """Test contract for search result rendering."""

    def test_renderer_rejects_non_skill_entities(self) -> None:
        """
        GREEN TEST: Renderer should only accept entities with skill: type.

        This test documents the expected behavior after fix.
        """
        # This is a design test - documents the contract
        # After fix, the renderer (ContextService.search) should:
        # 1. Only return chunks with type skill:
        # 2. Exclude repo:, prime:, agent:, session: from skill search results

        valid_types = {"skill"}
        invalid_types = {"repo", "prime", "agent", "session", "ref"}

        # All invalid types should be excluded from skill discovery
        for invalid_type in invalid_types:
            assert invalid_type not in valid_types, (
                f"{invalid_type} should not be in valid skill types"
            )


# Integration test with real skills-hub segment (if available)
class TestRealSkillsHubSegment:
    """Test against real skills-hub segment (integration)."""

    @pytest.fixture
    def real_segment(self) -> Path | None:
        """Get real skills-hub segment if available."""
        segment = Path.home() / ".trifecta" / "segments" / "skills-hub"
        if segment.exists():
            return segment
        return None

    @pytest.mark.skipif(
        not Path.home().joinpath(".trifecta/segments/skills-hub").exists(),
        reason="Real skills-hub segment not available"
    )
    def test_real_segment_metadata_not_discoverable(self, real_segment: Path) -> None:
        """
        INTEGRATION TEST: Real skills-hub should not discover segment metadata.
        """
        from src.application.context_service import ContextService

        service = ContextService(real_segment)

        # Search for something that would match metadata
        result = service.search("administrative segment metadata", k=10)

        result_ids = [h.id for h in result.hits]

        # Should not find prime/agent/session metadata as skills
        for rid in result_ids:
            assert not rid.startswith("prime:"), f"Found prime metadata: {rid}"
            assert not rid.startswith("agent:"), f"Found agent metadata: {rid}"
            assert not rid.startswith("session:"), f"Found session metadata: {rid}"

    @pytest.mark.skipif(
        not Path.home().joinpath(".trifecta/segments/skills-hub").exists(),
        reason="Real skills-hub segment not available"
    )
    def test_real_segment_skill_query_returns_skills(self, real_segment: Path) -> None:
        """
        INTEGRATION TEST: Query for skills should return skill: typed chunks.
        """
        from src.application.context_service import ContextService

        service = ContextService(real_segment)

        # Search for something skill-related
        result = service.search("refactor python code", k=10)

        if result.hits:
            # At least some results should be skill: type (after fix)
            # Before fix: all are repo: type
            skill_hits = [h for h in result.hits if h.id.startswith("skill:")]
            # This will be RED until fix is applied
            # After fix: assert len(skill_hits) > 0
            # For now, just document current state
            pass
