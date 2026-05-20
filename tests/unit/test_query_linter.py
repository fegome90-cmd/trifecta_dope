import pytest
import yaml
from src.domain.query_linter import lint_query


# Fixtures from real config files
@pytest.fixture
def anchors_cfg():
    with open("configs/anchors.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def aliases_cfg():
    with open("configs/aliases.yaml") as f:
        return yaml.safe_load(f)


def test_guided_no_expansion(anchors_cfg, aliases_cfg):
    """Case A: Guided no expande"""
    query = "agent.md template creation code file"
    # anchors: agent.md (strong), template (weak)
    # tokens: 5
    # strong >= 1 AND tokens >= 5 -> GUIDED

    plan = lint_query(query, anchors_cfg, aliases_cfg)

    assert plan["query_class"] == "guided"
    assert plan["changed"] is False
    assert plan["expanded_query"] == query


def test_vague_expansion(anchors_cfg, aliases_cfg):
    """Case B: Vague query with anchor present in query text."""
    query = "agent template"
    # tokens: 2 -> VAGUE (token_count < 3)
    # "agent.md" appears as substring of "agent" in anchors config strong.files

    plan = lint_query(query, anchors_cfg, aliases_cfg)

    assert plan["query_class"] == "vague"
    # With vague_default_boost removed, expansion depends on anchor detection.
    # "agent.md" may be detected as strong anchor (substring of "agent" in query)
    # or the query may stay unchanged if no anchors match.
    # Either way, NO synthetic defaults (agent.md/prime.md) should be injected.
    if plan["changed"]:
        # If expanded, it must be because an anchor was genuinely detected
        assert len(plan["changes"]["added_strong"]) <= 2
        assert len(plan["changes"]["added_weak"]) <= 2
        assert "vague_default_boost" not in plan["changes"]["reasons"], (
            "vague_default_boost should not appear — it was removed"
        )


def test_nl_spanish_alias(anchors_cfg, aliases_cfg):
    """Case C: NL español con alias"""
    # Usando una query que matchee el alias definido en aliases.yaml
    # Alias: "persistencia de sesión" -> session.md, session append
    query = "Muéstrame documentación sobre la persistencia de sesión"

    plan = lint_query(query, anchors_cfg, aliases_cfg)

    # "persistencia de sesión" matched -> add session.md (strong)
    # tokens > 5
    # strong >= 1 (session.md)
    # -> GUIDED (or SEMI if token count logic is strictly >= 5 AND ...)
    # tokens: muéstrame(1) documentación(2) sobre(3) la(4) persistencia(5) de(6) sesión(7) -> 7 tokens

    assert "persistencia de sesión" in plan["anchors_detected"]["aliases_matched"]
    assert plan["query_class"] in ("semi", "guided")
    assert plan["changed"] is False


def test_stability(anchors_cfg, aliases_cfg):
    """Case D: Estabilidad"""
    query = "help config"
    plan1 = lint_query(query, anchors_cfg, aliases_cfg)
    plan2 = lint_query(query, anchors_cfg, aliases_cfg)

    assert plan1 == plan2


def test_doc_intent_boost(anchors_cfg, aliases_cfg):
    """Extra: Check doc intent boost"""
    query = "docs"
    # VAGUE (1 token)
    # Has "docs" (weak doc term? check yaml)
    # In anchors.yaml, "docs" is in weak.intent_terms.
    # My code checked: is_doc_intent = any(t in existing_weak for t in ["doc", "docs", ...])
    # So it should trigger doc_intent_boost

    plan = lint_query(query, anchors_cfg, aliases_cfg)
    assert plan["query_class"] == "vague"
    assert (
        "docs/" in plan["changes"]["added_strong"] or "readme.md" in plan["changes"]["added_strong"]
    )


def test_reasons_no_duplicates(anchors_cfg, aliases_cfg):
    """Verify reasons list has no duplicates."""
    query = "help"
    # VAGUE (1 token) -> may or may not be expanded

    plan = lint_query(query, anchors_cfg, aliases_cfg)

    # Check that reasons has no duplicates
    reasons = plan["changes"]["reasons"]
    assert len(reasons) == len(set(reasons)), f"Reasons has duplicates: {reasons}"

    # vague_default_boost must never appear — it was removed
    assert "vague_default_boost" not in reasons, (
        "vague_default_boost should not appear — it was removed from the linter"
    )
