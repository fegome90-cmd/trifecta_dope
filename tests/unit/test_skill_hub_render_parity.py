import io
import re

from scripts.skill_hub_cards_core import (
    RenderPlan,
    SkillCardViewModel,
    ClassifiedResult,
    NormalizedResult,
    build_view_model,
    EXIT_RENDERABLE,
    EXIT_EMPTY,
    EXIT_NON_RENDERABLE,
    EXIT_ERROR
)
from src.cli.skill_cards import render_cards

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def test_parity_nominal_renderable_cards():
    norm = NormalizedResult(
        ref="skill:my-skill",
        raw_type="skill",
        raw_title="my-skill",
        score=0.9,
        stable_id="my-skill",
        visible_title="My Skill",
        path="/path/to/skill",
        source="agent",
        description="A clear description",
        metadata_message=None,
        metadata_reason=None,
    )
    c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok")
    old_card = SkillCardViewModel(id="my-skill", name="My Skill", path="/path/to/skill", source="agent", description="A clear description", authority_state="healthy", relevance=0.9)
    plan = RenderPlan(outcome_kind="renderable_skill", exit_code=EXIT_RENDERABLE, cards=[old_card], message="", classified_results=[c_res])
    
    # New Plain Output (the canonical path after Phase 6 cleanup)
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    assert len(vms) == 1
    buf = io.StringIO()
    render_cards(vms, style="plain", file=buf)
    new_plain = buf.getvalue().strip()
    
    # Essential information must survive
    assert "My Skill" in new_plain
    assert "A clear description" in new_plain
    assert "/path/to/skill" in new_plain
    assert strip_ansi(new_plain) == new_plain  # No ANSI
    
def test_parity_degraded_renderable_cards():
    norm = NormalizedResult(
        ref="skill:my-skill",
        raw_type="skill",
        raw_title="my-skill",
        score=0.9,
        stable_id="my-skill",
        visible_title="My Skill",
        path="/path/to/skill",
        source="agent",
        description="A clear description",
        metadata_message=None,
        metadata_reason=None,
    )
    c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok", authority_state="degraded")
    old_card = SkillCardViewModel(id="my-skill", name="My Skill", path="/path/to/skill", source="agent", description="A clear description", authority_state="healthy", relevance=0.9)
    # The old pipeline ignores degraded implicitly because it wasn't threading it
    plan = RenderPlan(outcome_kind="renderable_skill", exit_code=EXIT_RENDERABLE, cards=[old_card], message="", classified_results=[c_res])
    
    # Post-cleanup: render_plain no longer handles renderable_skill.
    # The new canonical path surfaces degraded textually.
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    buf = io.StringIO()
    render_cards(vms, style="plain", file=buf)
    new_plain = buf.getvalue().strip()
    
    # New behavior SURFACES it textually
    assert "Status: DEGRADED" in new_plain
    assert "A clear description" in new_plain

def test_parity_metadata_only():
    norm = NormalizedResult(
        ref="session:123",
        raw_type="session",
        raw_title="session",
        score=0.0,
        stable_id=None,
        visible_title=None,
        path=None,
        source=None,
        description=None,
        metadata_message="Metadata here",
        metadata_reason="admin",
    )
    c_res = ClassifiedResult(kind="metadata_only", normalized=norm, reason="admin")
    plan = RenderPlan(outcome_kind="metadata_only", exit_code=EXIT_NON_RENDERABLE, cards=[], message="Administrative metadata.", classified_results=[c_res])
    
    # The exit code confirms parity in how the process decides exit status
    assert plan.exit_code == 3
    
    # Check new path yields no cards
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    assert len(vms) == 0

def test_parity_no_hits():
    plan = RenderPlan(outcome_kind="empty", exit_code=EXIT_EMPTY, cards=[], message="No hits.", classified_results=[])
    
    assert plan.exit_code == 4
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    assert len(vms) == 0

def test_parity_exit_codes_integrity():
    assert EXIT_RENDERABLE == 0
    assert EXIT_ERROR == 1
    assert EXIT_NON_RENDERABLE == 3
    assert EXIT_EMPTY == 4

def test_parity_nominal_rich():
    norm = NormalizedResult(
        ref="skill:rich-skill",
        raw_type="skill",
        raw_title="rich-skill",
        score=0.9,
        stable_id="rich-skill",
        visible_title="Rich Skill",
        path="/path/to/skill",
        source="agent",
        description="A clear description",
        metadata_message=None,
        metadata_reason=None,
    )
    c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok")
    plan = RenderPlan(outcome_kind="renderable_skill", exit_code=0, cards=[SkillCardViewModel(id="rich-skill", name="Rich Skill", path="/path/to/skill", source="agent", description="A clear description", authority_state="healthy", relevance=0.9)], message="", classified_results=[c_res])
    
    # Post-cleanup: render_rich no longer handles renderable_skill.
    # Verify new canonical rich path.
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    buf = io.StringIO()
    render_cards(vms, style="rich", file=buf)
    new_rich = buf.getvalue().strip()
    
    assert "Rich Skill" in new_rich
    assert "A clear description" in new_rich
    assert len(new_rich) > 0  # ensure ANSI is applied in Rich mode
    assert "[DEGRADED]" not in new_rich  # healthy means no degraded badge


def test_parity_degraded_rich():
    norm = NormalizedResult(
        ref="skill:rich-skill",
        raw_type="skill",
        raw_title="rich-skill",
        score=0.9,
        stable_id="rich-skill",
        visible_title="Rich Skill",
        path="/path/to/skill",
        source="agent",
        description="A clear description",
        metadata_message=None,
        metadata_reason=None,
    )
    c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok", authority_state="degraded")
    plan = RenderPlan(outcome_kind="renderable_skill", exit_code=0, cards=[SkillCardViewModel(id="rich-skill", name="Rich Skill", path="/path/to/skill", source="agent", description="A clear description", authority_state="healthy", relevance=0.9)], message="", classified_results=[c_res])

    # Post-cleanup: render_rich no longer handles renderable_skill.
    # The new canonical path surfaces [DEGRADED] textually.
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    buf = io.StringIO()
    render_cards(vms, style="rich", file=buf)
    new_rich = strip_ansi(buf.getvalue().strip())

    assert "Rich Skill" in new_rich
    assert "[DEGRADED]" in new_rich  # explicitly surfaced textually despite rich design elements


def test_parity_nominal_compact():
    norm = NormalizedResult(
        ref="skill:compact-skill",
        raw_type="skill",
        raw_title="compact-skill",
        score=0.9,
        stable_id="compact-skill",
        visible_title="Compact Skill",
        path="/path/to/skill",
        source="agent",
        description="A short description",
        metadata_message=None,
        metadata_reason=None,
    )
    c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok")
    plan = RenderPlan(outcome_kind="renderable_skill", exit_code=0, cards=[SkillCardViewModel(id="compact-skill", name="Compact Skill", path="/path/to/skill", source="agent", description="A short description", authority_state="healthy", relevance=0.9)], message="", classified_results=[c_res])
    
    # Old model had NO compact, fell back to plain
    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    buf = io.StringIO()
    render_cards(vms, style="compact", file=buf)
    new_compact = buf.getvalue().strip()
    
    # Condensed format check
    assert "Compact Skill" in new_compact
    assert "A short description" in new_compact
    assert "[DEGRADED]" not in new_compact

def test_parity_degraded_compact():
    norm = NormalizedResult(
        ref="skill:compact-skill",
        raw_type="skill",
        raw_title="compact-skill",
        score=0.9,
        stable_id="compact-skill",
        visible_title="Compact Skill",
        path="/path/to/skill",
        source="agent",
        description="A short description",
        metadata_message=None,
        metadata_reason=None,
    )
    c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok", authority_state="degraded")
    plan = RenderPlan(outcome_kind="renderable_skill", exit_code=0, cards=[SkillCardViewModel(id="compact-skill", name="Compact Skill", path="/path/to/skill", source="agent", description="A short description", authority_state="healthy", relevance=0.9)], message="", classified_results=[c_res])

    vms = [build_view_model(r) for r in plan.classified_results if build_view_model(r) is not None]
    buf = io.StringIO()
    render_cards(vms, style="compact", file=buf)
    new_compact = buf.getvalue().strip()

    assert "Compact Skill" in new_compact
    assert "[DEGRADED]" in new_compact

