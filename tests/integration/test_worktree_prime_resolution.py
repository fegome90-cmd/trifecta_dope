"""Tests for worktree-compatible prime path resolution.

This module tests that prime file paths are resolved relative to segment root,
not REPO_ROOT, ensuring compatibility with git worktrees.

Context: Plan to fix prime path resolution in git worktrees.
See: docs/plans/2026-03-14-prime-path-worktree-fix.md
"""

from pathlib import Path

import pytest

from src.application.use_cases import BuildContextPackUseCase
from src.infrastructure.file_system import FileSystemAdapter


class TestWorktreePrimeResolution:
    """Test that prime paths work correctly in git worktrees."""

    def test_sync_in_worktree_resolves_segment_relative_paths(
        self, tmp_path: Path
    ) -> None:
        """Prime paths must be segment-relative, not REPO_ROOT-relative.

        This is the core fix: paths like 'skill.md' should resolve within
        the segment, regardless of whether we're in main repo or worktree.
        """
        # Setup: Create segment with segment-relative prime paths
        segment = tmp_path / "my_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Test\n\nSegment skill file.")
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Prime with segment-relative paths (NEW convention)
        (ctx_dir / "prime_my_segment.md").write_text("""---
segment: my_segment
profile: load_only
---

# Prime My Segment

> **SEGMENT_ROOT**: `.` (all paths relative to segment root)

## [HIGH] Prioridad ALTA

- `skill.md`
- `docs/guide.md`
""")
        (segment / "docs").mkdir()
        (segment / "docs" / "guide.md").write_text("# Guide\n\nDocumentation guide.")

        # Create config file
        import json

        config = {
            "segment": "my_segment",
            "scope": "Test segment",
            "repo_root": str(tmp_path),  # This should be IGNORED now
            "last_verified": "2026-03-14",
            "default_profile": "impl_patch",
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        # Execute: BuildContextPackUseCase should resolve paths within segment
        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(segment)

        # Verify: All paths resolved correctly
        assert result.is_ok(), f"Expected Ok, got Err: {result}"
        pack = result.unwrap()

        # Check that skill.md was indexed
        skill_chunks = [c for c in pack.chunks if "skill" in c.id.lower()]
        assert len(skill_chunks) > 0, "skill.md should be indexed"

        # Check that docs/guide.md was indexed
        guide_chunks = [c for c in pack.chunks if "guide" in c.id.lower()]
        assert len(guide_chunks) > 0, "docs/guide.md should be indexed"

    def test_old_style_prefixed_paths_not_found_in_segment(
        self, tmp_path: Path
    ) -> None:
        """Old-style 'segment_name/path' entries should not resolve.

        With the new convention, paths are relative to segment root.
        Old-style paths like 'my_segment/skill.md' won't exist within
        the segment (there's no my_segment/ subdirectory).
        """
        # Setup: Create segment with OLD-style paths (prefixed)
        segment = tmp_path / "my_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Test\n\nSegment skill file.")
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # OLD convention: path prefixed with segment name
        # This file DOES exist at segment/skill.md
        # But the path 'my_segment/skill.md' would look for:
        # segment/my_segment/skill.md which does NOT exist
        (ctx_dir / "prime_my_segment.md").write_text("""---
segment: my_segment
profile: load_only
---

# Prime My Segment (OLD CONVENTION)

> **REPO_ROOT**: `/some/parent/dir`

## [HIGH] Prioridad ALTA

- `my_segment/skill.md`
""")

        # Create config file
        import json

        config = {
            "segment": "my_segment",
            "scope": "Test segment",
            "repo_root": str(tmp_path),
            "last_verified": "2026-03-14",
            "default_profile": "impl_patch",
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        # Execute: Should work but the old-style path won't resolve
        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(segment)

        # Verify: Build succeeds but the old-style path isn't found
        # (The path my_segment/skill.md doesn't exist within the segment)
        assert result.is_ok(), f"Expected Ok, got Err: {result}"
        pack = result.unwrap()

        # The skill.md reference won't be in ref: chunks because
        # my_segment/skill.md doesn't exist within the segment
        ref_chunks = [c for c in pack.chunks if c.id.startswith("ref:")]
        # Old-style path wasn't resolved
        assert len(ref_chunks) == 0, "Old-style prefixed path should not resolve"

    def test_security_check_rejects_paths_outside_segment(
        self, tmp_path: Path
    ) -> None:
        """Security boundary must reject paths that escape segment.

        Even if someone puts an absolute path or ../.. in the prime file,
        it must be rejected by the security check.
        """
        segment = tmp_path / "my_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Test")
        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()

        # Create a file outside the segment
        outside_file = tmp_path / "secret.md"
        outside_file.write_text("# Secret\n\nThis is outside the segment.")

        # Prime with path that tries to escape
        (ctx_dir / "prime_my_segment.md").write_text("""---
segment: my_segment
profile: load_only
---

# Prime My Segment

- `../secret.md`
""")

        # Create config file
        import json

        config = {
            "segment": "my_segment",
            "scope": "Test segment",
            "repo_root": str(tmp_path),
            "last_verified": "2026-03-14",
            "default_profile": "impl_patch",
        }
        (ctx_dir / "trifecta_config.json").write_text(json.dumps(config))

        # Execute: Should fail with security error
        use_case = BuildContextPackUseCase(FileSystemAdapter())

        with pytest.raises(ValueError, match="PROHIBITED|outside segment"):
            use_case.execute(segment)

    def test_scan_docs_returns_segment_relative_paths(
        self, tmp_path: Path
    ) -> None:
        """scan_docs() should return paths relative to segment, not repo root.

        This tests the fix in file_system.py line 43.
        """
        # Setup: Create a segment with nested docs
        segment = tmp_path / "my_segment"
        segment.mkdir()
        docs_dir = segment / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide")
        (docs_dir / "api.md").write_text("# API")

        # Execute: scan_docs with segment as scan_path
        fs = FileSystemAdapter()
        docs = fs.scan_docs(scan_path=segment, repo_root=tmp_path)

        # Verify: Paths are relative to segment (scan_path), not repo_root
        assert "docs/guide.md" in docs, "Path should be relative to segment"
        assert "docs/api.md" in docs, "Path should be relative to segment"
        # Should NOT be prefixed with segment name
        assert not any(
            d.startswith("my_segment/") for d in docs
        ), f"Paths should not be prefixed with segment name: {docs}"


class TestPrimeTemplateGeneration:
    """Test that prime template generates segment-relative paths."""

    def test_render_prime_uses_segment_root_not_repo_root(self) -> None:
        """render_prime() should document that paths are segment-relative."""
        from src.domain.models import TrifectaConfig
        from src.infrastructure.templates import TemplateRenderer

        config = TrifectaConfig(
            segment="test_segment",
            scope="Test scope",
            repo_root="/some/parent/dir",  # This should be de-emphasized
            last_verified="2026-03-14",
        )

        renderer = TemplateRenderer()
        prime_content = renderer.render_prime(config, docs=["skill.md", "docs/guide.md"])

        # Verify: SEGMENT_ROOT is mentioned (not just REPO_ROOT)
        # The new convention should be clear
        assert "SEGMENT_ROOT" in prime_content or (
            "relativa" in prime_content.lower() and "segment" in prime_content.lower()
        ), "Prime should document segment-relative paths"

        # Verify: Docs are listed without segment prefix
        assert "`skill.md`" in prime_content, "skill.md should be listed"
        assert "`docs/guide.md`" in prime_content, "docs/guide.md should be listed"
