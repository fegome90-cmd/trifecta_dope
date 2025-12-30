"""Test suite for Session Evidence Persistence protocol in templates."""

import pytest
from src.domain.models import TrifectaConfig
from src.infrastructure.templates import TemplateRenderer


def test_render_session_contains_session_log():
    """Verify that render_session() contains 'Session Log (append-only)'."""
    renderer = TemplateRenderer()
    config = TrifectaConfig(
        segment="test",
        scope="Test segment",
        repo_root="/tmp/test",
        last_verified="2025-12-29",
        default_profile="impl_patch"
    )
    
    output = renderer.render_session(config)
    
    assert "Session Log (append-only)" in output
    assert "Entry Template (max 12 lines)" in output
    assert "YYYY-MM-DD HH:MM - ctx cycle" in output
    assert "append-only" in output


def test_render_skill_contains_session_evidence_persistence():
    """Verify that render_skill() contains 'Session Evidence Persistence (Trifecta)'."""
    renderer = TemplateRenderer()
    config = TrifectaConfig(
        segment="test",
        scope="Test segment",
        repo_root="/tmp/test",
        last_verified="2025-12-29",
        default_profile="impl_patch"
    )
    
    output = renderer.render_skill(config)
    
    assert "Session Evidence Persistence (Trifecta)" in output
    assert "PERSISTE intencion minima" in output
    assert "SYNC del segmento" in output
    assert "LEE lo que acabas de escribir" in output
    assert "EJECUTA el ciclo de contexto" in output
    assert "REGISTRA resultado" in output


def test_no_forbidden_strings_in_templates():
    """Verify that no forbidden strings appear in templates."""
    renderer = TemplateRenderer()
    config = TrifectaConfig(
        segment="test",
        scope="Test segment",
        repo_root="/tmp/test",
        last_verified="2025-12-29",
        default_profile="impl_patch"
    )
    
    skill_output = renderer.render_skill(config)
    session_output = renderer.render_session(config)
    readme_output = renderer.render_readme(config)
    
    forbidden_strings = [
        "ingest_trifecta.py",
        "fork_summary_user_prompts.md",
        "History Persistence",  # Old protocol name
    ]
    
    for forbidden in forbidden_strings:
        assert forbidden not in skill_output, f"Found forbidden string '{forbidden}' in skill.md"
        assert forbidden not in session_output, f"Found forbidden string '{forbidden}' in session.md"
        assert forbidden not in readme_output, f"Found forbidden string '{forbidden}' in readme.md"


def test_session_template_has_correct_structure():
    """Verify that the session entry template has the correct structure."""
    renderer = TemplateRenderer()
    config = TrifectaConfig(
        segment="test",
        scope="Test segment",
        repo_root="/tmp/test",
        last_verified="2025-12-29",
        default_profile="impl_patch"
    )
    
    output = renderer.render_session(config)
    
    # Check for required fields in template
    required_fields = [
        "Segment:",
        "Objective:",
        "Plan:",
        "Commands:",
        "Evidence:",
        "Warnings:",
        "Next:"
    ]
    
    for field in required_fields:
        assert field in output, f"Missing required field '{field}' in session template"


def test_skill_protocol_has_5_steps():
    """Verify that the Session Evidence Persistence protocol has 5 numbered steps."""
    renderer = TemplateRenderer()
    config = TrifectaConfig(
        segment="test",
        scope="Test segment",
        repo_root="/tmp/test",
        last_verified="2025-12-29",
        default_profile="impl_patch"
    )
    
    output = renderer.render_skill(config)
    
    # Check for 5 numbered steps
    for i in range(1, 6):
        assert f"{i})" in output, f"Missing step {i} in Session Evidence Persistence protocol"
    
    # Check for "Prohibido:" section
    assert "Prohibido:" in output
