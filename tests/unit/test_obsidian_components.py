"""Tests for HookifyExtractor and NoteRenderer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.application.hookify_extractor import HookifyExtractor, RULE_METADATA
from src.application.obsidian_renderer import NoteRenderer
from src.domain.obsidian_models import Finding
from src.infrastructure.hookify_logger import HookifyViolation


@pytest.fixture
def temp_segment_root(tmp_path: Path) -> Path:
    """Create a temporary segment root."""
    segment = tmp_path / "segment"
    segment.mkdir()
    return segment


@pytest.fixture
def extractor(temp_segment_root: Path) -> HookifyExtractor:
    """Create an extractor instance."""
    return HookifyExtractor(temp_segment_root)


@pytest.fixture
def renderer() -> NoteRenderer:
    """Create a renderer instance."""
    return NoteRenderer()


@pytest.fixture
def sample_violation() -> HookifyViolation:
    """Create a sample violation."""
    return HookifyViolation(
        id="violation-1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        rule_name="metodo-p1-stringly-typed",
        pattern_matched="in str(",
        context={
            "file_path": "src/main.py",
            "line": "42",
        },
    )


class TestRuleMetadata:
    """Tests for RULE_METADATA registry."""

    def test_p1_rule_exists(self):
        """Test P1 rule is registered."""
        assert "metodo-p1-stringly-typed" in RULE_METADATA
        metadata = RULE_METADATA["metodo-p1-stringly-typed"]
        assert metadata.priority == "P1"
        assert metadata.category == "code-quality"

    def test_p0_rule_exists(self):
        """Test P0 security rule is registered."""
        assert "hardcoded-secrets" in RULE_METADATA
        metadata = RULE_METADATA["hardcoded-secrets"]
        assert metadata.priority == "P0"
        assert metadata.category == "security"

    def test_all_rule_priorities_valid(self):
        """Test all rule priorities are valid."""
        valid_priorities = {"P0", "P1", "P2", "P3", "P4", "P5"}
        for rule_name, metadata in RULE_METADATA.items():
            assert metadata.priority in valid_priorities, f"{rule_name} has invalid priority"


class TestHookifyExtractor:
    """Tests for HookifyExtractor."""

    def test_extract_single_violation(self, extractor, sample_violation):
        """Test extracting a single violation."""
        findings = extractor.extract([sample_violation])
        assert len(findings) == 1

        finding = findings[0]
        assert finding.id == "violation-1"
        assert finding.priority == "P1"
        assert finding.category == "code-quality"
        assert finding.metadata.detected_by == "hookify"

    def test_filter_by_min_priority(self, extractor):
        """Test filtering by minimum priority."""
        p5_violation = HookifyViolation(
            id="v1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rule_name="metodo-p5-env-precedence",
            pattern_matched="test",
            context={},
        )
        p1_violation = HookifyViolation(
            id="v2",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rule_name="metodo-p1-stringly-typed",
            pattern_matched="test",
            context={},
        )

        # Only get P1 and above
        findings = extractor.extract([p5_violation, p1_violation], min_priority="P1")
        assert len(findings) == 1
        assert findings[0].id == "v2"

    def test_p0_always_included(self, extractor):
        """Test P0 findings are always included."""
        p0_violation = HookifyViolation(
            id="critical-1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rule_name="hardcoded-secrets",
            pattern_matched='api_key = "',
            context={},
        )

        findings = extractor.extract([p0_violation], min_priority="P1")
        assert len(findings) == 1
        assert findings[0].priority == "P0"

    def test_skip_ignored_violations(self, extractor):
        """Test ignored violations are skipped."""
        violation = HookifyViolation(
            id="v1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rule_name="metodo-p1-stringly-typed",
            pattern_matched="test",
            context={},
            status="ignored",
        )

        findings = extractor.extract([violation])
        assert len(findings) == 0

    def test_skip_unknown_rules(self, extractor):
        """Test violations with unknown rules are skipped."""
        violation = HookifyViolation(
            id="v1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rule_name="unknown-rule",
            pattern_matched="test",
            context={},
        )

        findings = extractor.extract([violation])
        assert len(findings) == 0

    def test_finding_has_required_fields(self, extractor, sample_violation):
        """Test extracted finding has all required fields."""
        findings = extractor.extract([sample_violation])
        finding = findings[0]

        assert finding.id == sample_violation.id
        assert finding.title
        assert finding.summary
        assert finding.description
        assert finding.risk
        assert finding.effort
        assert finding.traceability is not None
        assert finding.evidence is not None
        assert finding.metadata is not None
        assert len(finding.actions) > 0

    def test_finding_tags(self, extractor, sample_violation):
        """Test finding has proper tags."""
        findings = extractor.extract([sample_violation])
        finding = findings[0]

        assert "finding/P1" in finding.tags
        assert "pattern/P1-Stringly-Typed" in finding.tags
        assert "source/hookify" in finding.tags
        assert "adr/001" in finding.tags

    def test_priority_order_check(self, extractor):
        """Test priority comparison works correctly."""
        # P0 < P1 < P2 < P3 < P4 < P5
        assert extractor._priority_meets_min("P1", "P1") is True
        assert extractor._priority_meets_min("P1", "P2") is True
        assert extractor._priority_meets_min("P2", "P1") is False
        assert extractor._priority_meets_min("P0", "P1") is True
        assert extractor._priority_meets_min("P5", "P4") is False


class TestNoteRenderer:
    """Tests for NoteRenderer."""

    @pytest.fixture
    def sample_finding(self) -> Finding:
        """Create a sample finding."""
        return Finding(
            id="test-1",
            title="[P1] Metodo P1 Stringly Typed",
            priority="P1",
            category="code-quality",
            status="open",
            created=datetime(2026, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            segment="test-segment",
            segment_id="abc123",
            tags=["finding/P1", "adr/001"],
            risk="High risk",
            effort="30 min",
            summary="Test summary",
            description="Test description\n\nMore details here.",
        )

    def test_generate_filename(self, renderer, sample_finding):
        """Test filename generation."""
        note = renderer.render(sample_finding, Path("/vault"))
        assert note.filename == "2026-01-03-P1-test-1.md"

    def test_render_frontmatter(self, renderer, sample_finding):
        """Test frontmatter rendering."""
        note = renderer.render(sample_finding, Path("/vault"))
        frontmatter = note.frontmatter

        assert frontmatter["id"] == "test-1"
        assert frontmatter["title"] == sample_finding.title
        assert frontmatter["priority"] == "P1"
        assert frontmatter["status"] == "open"
        assert frontmatter["segment"] == "test-segment"
        assert "finding/P1" in frontmatter["tags"]

    def test_render_body(self, renderer, sample_finding):
        """Test body rendering."""
        note = renderer.render(sample_finding, Path("/vault"))
        content = note.content

        assert "# [P1] Metodo P1 Stringly Typed" in content
        assert "## Summary" in content
        assert "## Risk" in content
        assert "## Details" in content

    def test_render_full_note(self, renderer, sample_finding):
        """Test full note rendering with frontmatter and body."""
        note = renderer.render(sample_finding, Path("/vault"))
        rendered = note.render()

        assert "---" in rendered
        assert "id: test-1" in rendered
        assert "# [P1] Metodo P1 Stringly Typed" in rendered
        assert "---\n\n" in rendered  # Frontmatter separator

    def test_render_with_traceability(self, renderer):
        """Test rendering with traceability info."""
        from src.domain.obsidian_models import FindingTraceability

        finding = Finding(
            id="test-2",
            title="Test",
            priority="P2",
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
            traceability=FindingTraceability(
                hookify_rule="test-rule",
                location="src/file.py:42",
            ),
        )

        note = renderer.render(finding, Path("/vault"))
        content = note.content
        assert "test-rule" in content
        assert "src/file.py:42" in content

    def test_render_with_evidence(self, renderer):
        """Test rendering with evidence."""
        from src.domain.obsidian_models import FindingEvidence

        finding = Finding(
            id="test-3",
            title="Test",
            priority="P2",
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
            evidence=FindingEvidence(
                pattern="in str(",
                context={"line": "42"},
            ),
        )

        note = renderer.render(finding, Path("/vault"))
        content = note.content
        assert "in str(" in content
        assert "line: 42" in content

    def test_render_with_actions(self, renderer):
        """Test rendering with action items."""
        from src.domain.obsidian_models import FindingAction

        finding = Finding(
            id="test-4",
            title="Test",
            priority="P2",
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
            actions=[
                FindingAction(
                    type="code",
                    description="Fix the bug",
                    estimate="30 min",
                ),
                FindingAction(
                    type="test",
                    description="Add tests",
                    estimate="15 min",
                ),
            ],
        )

        note = renderer.render(finding, Path("/vault"))
        content = note.content
        assert "## Actions" in content
        assert "[ ] **code**: Fix the bug" in content
        assert "[ ] **test**: Add tests" in content
