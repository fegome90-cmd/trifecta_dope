from scripts.skill_hub_cards_core import ClassifiedResult, NormalizedResult, build_view_model

def test_build_view_model_success():
    normalized = NormalizedResult(
        ref="skill:my-skill.md",
        raw_type="skill",
        raw_title="My Skill",
        score=0.9,
        stable_id="my-skill",
        visible_title="My Visible Skill",
        path="/some/path",
        source="agent",
        description="a description",
        metadata_message=None,
        metadata_reason=None,
        authority_state="degraded"
    )
    classified = ClassifiedResult(
        kind="renderable_skill",
        normalized=normalized,
        reason="ok"
    )
    
    vm = build_view_model(classified)
    
    assert vm is not None
    assert vm.id == "my-skill"
    assert vm.name == "My Visible Skill"
    assert vm.id != vm.name
    assert vm.authority_state == "degraded"
    assert vm.path == "/some/path"
    assert vm.source == "agent"
    assert vm.description == "a description"
    assert vm.relevance == 0.9

def test_build_view_model_authority_state_healthy_fallback():
    normalized = NormalizedResult(
        ref="skill:my-skill.md",
        raw_type="skill",
        raw_title="My Skill",
        score=0.9,
        stable_id="my-skill",
        visible_title="My Visible Skill",
        path="/some/path",
        source="agent",
        description="a description",
        metadata_message=None,
        metadata_reason=None,
        authority_state="some-invalid-state"
    )
    classified = ClassifiedResult(
        kind="renderable_skill",
        normalized=normalized,
        reason="ok"
    )
    
    vm = build_view_model(classified)
    
    assert vm is not None
    assert vm.authority_state == "healthy" # Enforces strictly "healthy" or "degraded" without inferring "degraded".

def test_build_view_model_unsupported():
    normalized = NormalizedResult(
        ref="session:abc",
        raw_type="session",
        raw_title="session",
        score=0.1,
        stable_id=None,
        visible_title=None,
        path=None,
        source=None,
        description=None,
        metadata_message=None,
        metadata_reason=None,
        authority_state="healthy"
    )
    classified = ClassifiedResult(
        kind="metadata_only",
        normalized=normalized,
        reason="ok"
    )
    vm = build_view_model(classified)
    assert vm is None
