"""Unit tests for path guardrails.

Tests cover:
- canonicalize_path
- ensure_within_root (path traversal prevention)
- validate_wo_id
- segment validation
- symlink escape prevention
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.path_utils import (
    PathTraversalError,
    InvalidSegmentError,
    canonicalize_path,
    ensure_within_root,
    validate_wo_id,
    validate_segment,
    validate_segment_exists,
    validate_segment_has_ctx,
    validate_segment_is_git_repo,
)


class TestCanonicalizePath:
    """Tests for canonicalize_path function."""

    def test_canonicalize_absolute_path(self):
        """Absolute paths should resolve to themselves."""
        path = canonicalize_path("/tmp")
        assert path.is_absolute()
        assert path == Path("/tmp").resolve()

    def test_canonicalize_relative_path(self):
        """Relative paths should become absolute."""
        path = canonicalize_path(".")
        assert path.is_absolute()

    def test_canonicalize_expand_user(self):
        """Tilde should expand to home directory."""
        path = canonicalize_path("~")
        assert path.home() in path.parents or path == path.home()

    def test_canonicalize_empty_raises(self):
        """Empty path should raise ValueError."""
        with pytest.raises(ValueError, match="Empty path"):
            canonicalize_path("")

    def test_canonicalize_dots_resolved(self):
        """Dot segments should be resolved."""
        path = canonicalize_path("./foo/../bar")
        assert path.name == "bar"
        assert ". ." not in str(path)


class TestEnsureWithinRoot:
    """Tests for ensure_within_root (path traversal prevention)."""

    def test_allow_subpath_within_root(self):
        """Subpath within root should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subdir = root / "subdir"
            subdir.mkdir()

            result = ensure_within_root(subdir, root)
            assert result == subdir.resolve()

    def test_block_path_traversal(self):
        """Path traversal with ../ should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sibling = root.parent / "sibling"

            with pytest.raises(PathTraversalError):
                ensure_within_root(sibling, root)

    def test_block_deep_traversal(self):
        """Deep traversal attempts should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            escape = root / ".." / ".." / "etc"

            with pytest.raises(PathTraversalError):
                ensure_within_root(escape, root)

    def test_block_absolute_escape(self):
        """Absolute path outside root should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outside = Path("/tmp")

            with pytest.raises(PathTraversalError):
                ensure_within_root(outside, root)

    def test_block_symlink_escape(self):
        """Symlink pointing outside root should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outside_target = Path("/tmp")

            # Create symlink in root pointing to outside
            symlink = root / "escape_link"
            if not symlink.exists():
                try:
                    symlink.symlink_to(outside_target)
                except OSError:
                    pytest.skip("Cannot create symlink")

            with pytest.raises(PathTraversalError):
                ensure_within_root(symlink, root)

    def test_same_path_allowed(self):
        """Path equal to root should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            result = ensure_within_root(root, root)
            assert result == root.resolve()


class TestValidateWoId:
    """Tests for validate_wo_id function."""

    def test_valid_wo_id(self):
        """Valid WO ID should pass."""
        assert validate_wo_id("WO-0053") == "WO-0053"
        assert validate_wo_id("WO-0001") == "WO-0001"
        assert validate_wo_id("WO-9999") == "WO-9999"

    def test_invalid_wo_id_no_dash(self):
        """Missing dash should fail."""
        with pytest.raises(ValueError, match="Invalid WO ID"):
            validate_wo_id("WO0053")

    def test_invalid_wo_id_lowercase(self):
        """Lowercase should fail."""
        with pytest.raises(ValueError, match="Invalid WO ID"):
            validate_wo_id("wo-0053")

    def test_invalid_wo_id_short(self):
        """Short number should fail."""
        with pytest.raises(ValueError, match="Invalid WO ID"):
            validate_wo_id("WO-53")

    def test_invalid_wo_id_long(self):
        """Long number should fail."""
        with pytest.raises(ValueError, match="Invalid WO ID"):
            validate_wo_id("WO-00533")

    def test_invalid_wo_id_underscore(self):
        """Underscore should fail."""
        with pytest.raises(ValueError, match="Invalid WO ID"):
            validate_wo_id("WO_0053")

    def test_invalid_wo_id_path_traversal(self):
        """Path traversal in WO ID should fail."""
        with pytest.raises(ValueError, match="Invalid WO ID"):
            validate_wo_id("../../WO-0053")

    def test_empty_wo_id(self):
        """Empty WO ID should fail."""
        with pytest.raises(ValueError, match="Empty WO ID"):
            validate_wo_id("")


class TestValidateSegment:
    """Tests for segment validation functions."""

    def test_segment_exists(self):
        """Existing path should pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_segment_exists(tmpdir)
            assert result.is_absolute()

    def test_segment_not_exists(self):
        """Non-existing path should fail."""
        with pytest.raises(InvalidSegmentError, match="does not exist"):
            validate_segment_exists("/nonexistent/path/12345")

    def test_segment_is_git_repo(self):
        """Git repository should pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            result = validate_segment_is_git_repo(tmpdir)
            assert result.is_absolute()

    def test_segment_not_git_repo(self):
        """Non-git path should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(InvalidSegmentError, match="not a git repository"):
                validate_segment_is_git_repo(tmpdir)

    def test_segment_has_ctx(self):
        """Path with _ctx should pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx_dir = Path(tmpdir) / "_ctx"
            ctx_dir.mkdir()

            result = validate_segment_has_ctx(tmpdir)
            assert result.is_absolute()

    def test_segment_no_ctx(self):
        """Path without _ctx should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(InvalidSegmentError, match="not a Trifecta segment"):
                validate_segment_has_ctx(tmpdir)

    def test_validate_segment_full(self):
        """Full validation with all options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()
            ctx_dir = Path(tmpdir) / "_ctx"
            ctx_dir.mkdir()

            result = validate_segment(
                tmpdir,
                require_git=True,
                require_ctx=True,
            )
            assert result.is_absolute()

    def test_validate_segment_fails_git(self):
        """Validation fails when require_git=True but no .git."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx_dir = Path(tmpdir) / "_ctx"
            ctx_dir.mkdir()

            with pytest.raises(InvalidSegmentError, match="not a git repository"):
                validate_segment(tmpdir, require_git=True, require_ctx=True)


class TestIntegration:
    """Integration tests for security boundaries."""

    def test_real_path_traversal_attempt(self):
        """Real path traversal attack should be blocked."""
        # This simulates an attacker trying: trifecta --segment /etc/../../root
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Attacker tries to escape
            malicious = root / ".." / ".." / ".." / "etc"

            with pytest.raises(PathTraversalError):
                ensure_within_root(malicious, root)

    def test_canonicalization_prevents_double_dot(self):
        """Canonicalization should resolve .. before validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subdir = root / "a" / "b"
            subdir.mkdir(parents=True)

            # Try: root/a/../../../etc
            escape = root / "a" / ".." / ".." / "etc"

            # Should be blocked because canonical path is outside
            with pytest.raises(PathTraversalError):
                ensure_within_root(escape, root)
