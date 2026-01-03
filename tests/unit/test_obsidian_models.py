"""Tests for Obsidian domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.obsidian_models import (
    Finding,
    FindingAction,
    FindingEvidence,
    FindingMetadata,
    FindingRelated,
    FindingTraceability,
    ObsidianConfig,
    ObsidianNote,
    SyncResult,
    ValidationResult,
)


class TestObsidianConfig:
    """Tests for ObsidianConfig."""

    def test_create_config(self):
        """Test creating a config."""
        from pathlib import Path

        config = ObsidianConfig(
            vault_path=Path("/vault"),
            min_priority="P2",
        )
        assert config.vault_path == Path("/vault")
        assert config.min_priority == "P2"
        assert config.note_folder == "Trifecta Findings"

    def test_p0_priority_supported(self):
        """Test P0 priority is supported."""
        from pathlib import Path

        config = ObsidianConfig(
            vault_path=Path("/vault"),
            min_priority="P0",
        )
        assert config.min_priority == "P0"

    def test_findings_dir_property(self):
        """Test findings_dir property."""
        from pathlib import Path

        config = ObsidianConfig(
            vault_path=Path("/vault"),
            note_folder="Custom",
        )
        assert config.findings_dir == Path("/vault/Custom")


class TestFindingAction:
    """Tests for FindingAction."""

    def test_create_action(self):
        """Test creating an action."""
        action = FindingAction(
            type="code",
            description="Fix the bug",
            estimate="30 min",
        )
        assert action.type == "code"
        assert action.files == []


class TestFindingTraceability:
    """Tests for FindingTraceability."""

    def test_create_traceability(self):
        """Test creating traceability info."""
        trace = FindingTraceability(
            hookify_rule="test-rule",
            location="src/file.py:42",
        )
        assert trace.hookify_rule == "test-rule"
        assert trace.commit is None


class TestFindingEvidence:
    """Tests for FindingEvidence."""

    def test_create_evidence(self):
        """Test creating evidence."""
        evidence = FindingEvidence(
            pattern="test-pattern",
            context={"file": "test.py"},
        )
        assert evidence.pattern == "test-pattern"
        assert evidence.scan_output is None


class TestFindingMetadata:
    """Tests for FindingMetadata."""

    def test_create_metadata(self):
        """Test creating metadata."""
        metadata = FindingMetadata(
            detected_by="hookify",
            adr="001",
        )
        assert metadata.detected_by == "hookify"
        assert metadata.adr == "001"


class TestFindingRelated:
    """Tests for FindingRelated."""

    def test_create_related(self):
        """Test creating related findings."""
        related = FindingRelated(
            blocks=["finding-1"],
            blocked_by=["finding-2"],
        )
        assert related.blocks == ["finding-1"]
        assert related.duplicates == []


class TestFinding:
    """Tests for Finding."""

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding for testing."""
        return Finding(
            id="test-1",
            title="Test Finding",
            priority="P1",
            category="code-quality",
            status="open",
            created=datetime.now(timezone.utc),
            segment="test-segment",
            segment_id="abc123",
            tags=["finding/P1"],
            risk="High risk",
            effort="30 min",
            summary="Test summary",
            description="Test description",
        )

    def test_create_finding(self, sample_finding):
        """Test creating a finding."""
        assert sample_finding.id == "test-1"
        assert sample_finding.priority == "P1"
        assert sample_finding.status == "open"

    def test_p0_priority_supported(self):
        """Test P0 priority is supported."""
        finding = Finding(
            id="critical-1",
            title="Critical Security Issue",
            priority="P0",
            category="security",
            status="open",
            created=datetime.now(timezone.utc),
            segment="test-segment",
            segment_id="abc123",
            tags=["finding/P0"],
            risk="CRITICAL",
            effort="1 hour",
            summary="Critical security issue",
            description="Hardcoded secret detected",
        )
        assert finding.priority == "P0"

    def test_to_dict(self, sample_finding):
        """Test converting finding to dict."""
        data = sample_finding.to_dict()
        assert data["id"] == "test-1"
        assert data["priority"] == "P1"
        assert isinstance(data["created"], str)

    def test_to_dict_with_nested_objects(self):
        """Test to_dict properly serializes nested objects."""
        trace = FindingTraceability(hookify_rule="test-rule")
        evidence = FindingEvidence(pattern="test-pattern")
        metadata = FindingMetadata(detected_by="hookify")
        action = FindingAction(type="code", description="Fix it")
        related = FindingRelated(blocks=["other-1"])

        finding = Finding(
            id="test-1",
            title="Test",
            priority="P1",
            category="test",
            status="open",
            created=datetime.now(timezone.utc),
            segment="test",
            segment_id="abc",
            tags=[],
            risk="low",
            effort="10 min",
            summary="test",
            description="test",
            traceability=trace,
            evidence=evidence,
            metadata=metadata,
            actions=[action],
            related=related,
        )

        data = finding.to_dict()
        assert data["traceability"]["hookify_rule"] == "test-rule"
        assert data["evidence"]["pattern"] == "test-pattern"
        assert data["metadata"]["detected_by"] == "hookify"
        assert len(data["actions"]) == 1
        assert data["actions"][0]["type"] == "code"
        assert data["related"]["blocks"] == ["other-1"]


class TestObsidianNote:
    """Tests for ObsidianNote."""

    def test_render_note(self):
        """Test rendering a note with frontmatter."""
        from pathlib import Path

        note = ObsidianNote(
            path=Path("/vault/test.md"),
            filename="test.md",
            frontmatter={"id": "test-1", "title": "Test"},
            content="# Test Content",
            created=datetime.now(timezone.utc),
            finding_id="test-1",
        )

        rendered = note.render()
        assert "---" in rendered
        assert "id: test-1" in rendered
        assert "# Test Content" in rendered


class TestSyncResult:
    """Tests for SyncResult."""

    def test_create_result(self):
        """Test creating a sync result."""
        result = SyncResult(
            total_findings=10,
            notes_created=8,
            notes_updated=2,
            notes_skipped=0,
            active_sources=["hookify"],
            duration_ms=100,
        )
        assert result.total_findings == 10
        assert result.total_notes == 10

    def test_total_notes_property(self):
        """Test total_notes property."""
        result = SyncResult(
            total_findings=10,
            notes_created=7,
            notes_updated=3,
            notes_skipped=0,
            active_sources=[],
            duration_ms=100,
        )
        assert result.total_notes == 10


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_valid_result(self):
        """Test creating a valid result."""
        from pathlib import Path

        result = ValidationResult(
            valid=True,
            writable=True,
            findings_dir=Path("/vault/findings"),
            existing_notes=5,
        )
        assert result.valid is True
        assert result.error is None

    def test_invalid_result(self):
        """Test creating an invalid result."""
        result = ValidationResult(
            valid=False,
            writable=False,
            error="Vault not found",
            findings_dir=None,
            existing_notes=0,
        )
        assert result.valid is False
        assert result.error == "Vault not found"
