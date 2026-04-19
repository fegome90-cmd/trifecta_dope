from scripts.skill_hub_cards_core import (
    RenderPlan,
    SkillCardViewModel,
    ClassifiedResult,
    NormalizedResult,
    _select_renderer,
    EXIT_RENDERABLE,
    EXIT_NON_RENDERABLE,
)
import re

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def _mock_plan(style: str, state: str = "healthy", outcome="renderable_skill") -> RenderPlan:
    norm = NormalizedResult(
        ref="skill:handover-test",
        raw_type="skill",
        raw_title="Handover Skill",
        score=0.95,
        stable_id="handover-skill",
        visible_title="Handover Skill",
        path="/path/to/handover",
        source="agent",
        description="A handover test.",
        metadata_message="Meta Admin" if outcome != "renderable_skill" else None,
        metadata_reason="Because" if outcome != "renderable_skill" else None,
        authority_state=state
    )
    if outcome == "renderable_skill":
        c_res = ClassifiedResult(kind="renderable_skill", normalized=norm, reason="ok")
        old_card = SkillCardViewModel(id="handover-skill", name="Handover Skill", path="/path/to/handover", source="agent", description="A handover test.", authority_state="healthy", relevance=0.95)
        return RenderPlan(outcome_kind="renderable_skill", exit_code=EXIT_RENDERABLE, cards=[old_card], message="", classified_results=[c_res])
    else:
        c_res = ClassifiedResult(kind="metadata_only", normalized=norm, reason="meta")
        return RenderPlan(outcome_kind="metadata_only", exit_code=EXIT_NON_RENDERABLE, cards=[], message="Administrative metadata only", classified_results=[c_res])


def test_handover_plain_nominal():
    plan = _mock_plan("plain", state="healthy")
    out = _select_renderer(plan, use_json=False, style="plain")
    assert "Handover Skil" in out
    assert "A handover test." in out
    assert strip_ansi(out) == out
    assert "[DEGRADED]" not in out

def test_handover_plain_degraded():
    plan = _mock_plan("plain", state="degraded")
    out = _select_renderer(plan, use_json=False, style="plain")
    assert "Handover Skil" in out
    assert "Status: DEGRADED" in out

def test_handover_rich_nominal():
    plan = _mock_plan("rich", state="healthy")
    out = _select_renderer(plan, use_json=False, style="rich")
    assert "Handover Skil" in out
    assert "[DEGRADED]" not in out

def test_handover_compact_degraded():
    plan = _mock_plan("compact", state="degraded")
    out = _select_renderer(plan, use_json=False, style="compact")
    assert "Handover Skil" in out
    assert "[DEGRADED]" in out

def test_handover_metadata_passthrough():
    plan = _mock_plan("plain", outcome="metadata_only")
    out = _select_renderer(plan, use_json=False, style="plain")
    assert "Administrative metadata only" in out

def test_handover_json():
    plan = _mock_plan("plain", state="healthy")
    out = _select_renderer(plan, use_json=True, style="plain")
    import json
    data = json.loads(out)
    assert data["outcome_kind"] == "renderable_skill"
    assert data["cards"][0]["name"] == "Handover Skill"

