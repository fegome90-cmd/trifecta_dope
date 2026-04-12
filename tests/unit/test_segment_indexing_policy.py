"""
Tests for SegmentIndexingPolicy domain model.

TDD Phase 1: RED - These tests should FAIL until implementation exists.

Contract:
- SSOT: Policy is defined ONLY in trifecta_config.json
- Default: GENERIC if no policy specified
- Values: "generic" | "skill_hub"

Author: Trifecta Team
Date: 2026-03-19
"""

import json
from pathlib import Path



class TestSegmentIndexingPolicyDetection:
    """Tests for policy detection from config."""

    def test_generic_is_default_when_no_config(self, tmp_path: Path) -> None:
        """
        RED TEST: When no trifecta_config.json exists, policy should be GENERIC.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        policy = SegmentIndexingPolicy.detect(tmp_path)

        assert policy == SegmentIndexingPolicy.GENERIC

    def test_generic_is_default_when_no_policy_field(self, tmp_path: Path) -> None:
        """
        RED TEST: When config exists but no indexing_policy field, default to GENERIC.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        config = {"segment_id": "test", "repo_root": str(tmp_path)}
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        policy = SegmentIndexingPolicy.detect(tmp_path)

        assert policy == SegmentIndexingPolicy.GENERIC

    def test_skill_hub_detected_when_configured(self, tmp_path: Path) -> None:
        """
        RED TEST: When indexing_policy is skill_hub, detect it.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        config = {
            "segment_id": "skills-hub",
            "repo_root": str(tmp_path),
            "indexing_policy": "skill_hub",
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        policy = SegmentIndexingPolicy.detect(tmp_path)

        assert policy == SegmentIndexingPolicy.SKILL_HUB

    def test_invalid_policy_falls_back_to_generic(self, tmp_path: Path) -> None:
        """
        RED TEST: Invalid policy value falls back to GENERIC (safe default).
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        config = {
            "segment_id": "test",
            "repo_root": str(tmp_path),
            "indexing_policy": "invalid_value",
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        policy = SegmentIndexingPolicy.detect(tmp_path)

        assert policy == SegmentIndexingPolicy.GENERIC

    def test_non_dict_json_falls_back_to_generic(self, tmp_path: Path) -> None:
        """
        P0 fix: Valid JSON array (non-dict) should not crash with AttributeError.
        Should fall back to GENERIC instead.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "trifecta_config.json").write_text("[]")

        policy = SegmentIndexingPolicy.detect(tmp_path)

        assert policy == SegmentIndexingPolicy.GENERIC

    def test_corrupt_config_falls_back_to_generic(self, tmp_path: Path) -> None:
        """
        RED TEST: Corrupt JSON in config falls back to GENERIC (fail-safe).
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / "trifecta_config.json").write_text("{ invalid json }")

        policy = SegmentIndexingPolicy.detect(tmp_path)

        assert policy == SegmentIndexingPolicy.GENERIC


class TestSegmentIndexingPolicyValues:
    """Tests for policy enum values."""

    def test_generic_value(self) -> None:
        """
        RED TEST: GENERIC should have value 'generic'.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        assert SegmentIndexingPolicy.GENERIC == "generic"

    def test_skill_hub_value(self) -> None:
        """
        RED TEST: SKILL_HUB should have value 'skill_hub'.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        assert SegmentIndexingPolicy.SKILL_HUB == "skill_hub"


class TestSegmentIndexingPolicyNoConflict:
    """Tests demonstrating no conflict is possible (SSOT)."""

    def test_only_config_is_source(self, tmp_path: Path) -> None:
        """
        RED TEST: Policy comes ONLY from config, not from manifest.

        This demonstrates that even if skills_manifest.json exists,
        it doesn't influence policy detection.
        """
        from src.domain.segment_indexing_policy import SegmentIndexingPolicy

        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()

        # Config says GENERIC
        config = {"segment_id": "test", "repo_root": str(tmp_path), "indexing_policy": "generic"}
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        # Manifest exists but should NOT influence policy
        manifest = {"schema_version": 2, "skills": []}
        (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest))

        policy = SegmentIndexingPolicy.detect(tmp_path)

        # Should be GENERIC from config, not influenced by manifest
        assert policy == SegmentIndexingPolicy.GENERIC