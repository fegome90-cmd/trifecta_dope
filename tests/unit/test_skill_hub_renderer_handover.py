from scripts.skill_hub_cards_core import (
    RenderPlan,
    ClassifiedResult,
    NormalizedResult,
    OutcomeKind,
    _select_renderer,
    build_view_model,
    EXIT_RENDERABLE,
    EXIT_NON_RENDERABLE,
)
import re

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def _mock_plan(style: str, state: str = "healthy", outcome: str = "renderable_skill") -> RenderPlan:
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
    )
    if outcome == "renderable_skill":
        c_res = ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=norm,
            reason="ok",
            authority_state=state,
        )
        vm = build_view_model(c_res)
        return RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=EXIT_RENDERABLE,
            cards=[vm] if vm else [],
            message="",
            classified_results=[c_res],
        )
    else:
        c_res = ClassifiedResult(
            kind=OutcomeKind.METADATA_ONLY,
            normalized=norm,
            reason="meta",
        )
        return RenderPlan(
            outcome_kind=OutcomeKind.METADATA_ONLY,
            exit_code=EXIT_NON_RENDERABLE,
            cards=[],
            message="Administrative metadata only",
            classified_results=[c_res],
        )


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
