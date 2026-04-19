import pytest

from src.application.skill_card_view_model import SkillCardViewModel


def test_skill_card_view_model_success():
    model = SkillCardViewModel(
        id="test-id",
        name="Test Name",
        path="/some/path",
        source="agent",
        description="test obj",
        authority_state="healthy"
    )
    assert model.id == "test-id"
    assert model.name == "Test Name"
    assert model.id != model.name
    assert model.authority_state == "healthy"


def test_skill_card_view_model_id_and_name_separation():
    model = SkillCardViewModel(
        id="id-123",
        name="User Visible Name",
        path="/path",
        source="x",
        description="desc",
        authority_state="degraded"
    )
    assert model.id == "id-123"
    assert model.name == "User Visible Name"


def test_skill_card_view_model_authority_state_must_be_strict():
    with pytest.raises(ValueError, match="authority_state must be 'healthy' or 'degraded'"):
        SkillCardViewModel(
            id="1",
            name="n",
            path="p",
            source="s",
            description="d",
            authority_state="invalid" # type: ignore
        )
    
    with pytest.raises(ValueError, match="authority_state must be 'healthy' or 'degraded'"):
        SkillCardViewModel(
            id="1",
            name="n",
            path="p",
            source="s",
            description="d",
            authority_state=None # type: ignore
        )

def test_skill_card_view_model_id_name_not_none():
    with pytest.raises(ValueError, match="id and name must be provided, not None"):
        SkillCardViewModel(
            id=None, # type: ignore
            name="n",
            path="p",
            source="s",
            description="d",
            authority_state="healthy"
        )
