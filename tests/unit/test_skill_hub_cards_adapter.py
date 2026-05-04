"""Card adapter + view model + renderer handoff tests (UX-001→UX-005).

Task 3.0: DELETE + REWRITE from scratch.
Tests cover: classify_result authority_state, build_view_model, renderer routing.
"""
import sys
from dataclasses import dataclass

import pytest

from scripts.skill_hub_cards_core import (
    ClassifiedResult,
    NormalizedResult,
    OutcomeKind,
    RenderPlan,
    SkillCard,
    build_view_model,
    classify_result,
)


# --- Helpers ---


def _full_normalized(**overrides) -> NormalizedResult:
    """Create a NormalizedResult with all 5 trusted fields present."""
    defaults = dict(
        ref="skill:python-patterns:abc123",
        raw_type="skill",
        raw_title="Python Patterns",
        score=0.85,
        stable_id="python-patterns",
        visible_title="Python Patterns",
        path="/skills/python-patterns/SKILL.md",
        source="claude-skills",
        description="Use when you need Python idioms and best practices.",
        metadata_message=None,
        metadata_reason=None,
    )
    defaults.update(overrides)
    return NormalizedResult(**defaults)


# --- Task 3.1: classify_result authority_state healthy (UX-001) ---


def test_classify_result_sets_authority_state_healthy():
    """All 5 trusted fields present → authority_state='healthy'."""
    normalized = _full_normalized()
    result = classify_result(normalized)

    assert result.kind == OutcomeKind.RENDERABLE_SKILL
    assert result.authority_state == "healthy"


# --- Task 3.2: classify_result authority_state degraded (UX-002) ---


def test_classify_result_sets_authority_state_degraded():
    """3 of 5 trusted fields → authority_state='degraded', kind=RENDERABLE_SKILL."""
    normalized = _full_normalized(
        path=None,
        description=None,
    )
    result = classify_result(normalized)

    assert result.kind == OutcomeKind.RENDERABLE_SKILL
    assert result.authority_state == "degraded"


# --- Task 3.4: build_view_model healthy (UX-001) ---


def test_build_view_model_healthy():
    """All 5 fields → fidelity_level='full', compact_flag=False."""
    classified = ClassifiedResult(
        kind=OutcomeKind.RENDERABLE_SKILL,
        normalized=_full_normalized(),
        reason="sufficient trusted fields",
        authority_state="healthy",
    )

    vm = build_view_model(classified)

    assert vm is not None
    assert vm.id == "python-patterns"
    assert vm.name == "Python Patterns"
    assert vm.path == "/skills/python-patterns/SKILL.md"
    assert vm.source == "claude-skills"
    assert vm.description == "Use when you need Python idioms and best practices."
    assert vm.authority_state == "healthy"
    assert vm.fidelity_level == "full"
    assert vm.compact_flag is False
    assert vm.relevance == 0.85


# --- Task 3.5: build_view_model degraded partial (UX-002) ---


def test_build_view_model_degraded_partial():
    """3 of 5 fields → fidelity_level='partial', compact_flag=True."""
    classified = ClassifiedResult(
        kind=OutcomeKind.RENDERABLE_SKILL,
        normalized=_full_normalized(path=None, description=None),
        reason="partial trusted fields",
        authority_state="degraded",
    )

    vm = build_view_model(classified)

    assert vm is not None
    assert vm.authority_state == "degraded"
    assert vm.fidelity_level == "partial"
    assert vm.compact_flag is True


# --- Task 3.5b: build_view_model non-renderable → None (UX-003) ---


def test_build_view_model_returns_none_for_non_renderable():
    """METADATA_ONLY → None."""
    classified = ClassifiedResult(
        kind=OutcomeKind.METADATA_ONLY,
        normalized=_full_normalized(),
        reason="metadata",
    )

    assert build_view_model(classified) is None


# --- Task 3.5c: build_view_model degraded minimal (UX-002) ---


def test_build_view_model_degraded_minimal():
    """1-2 of 5 fields (minimum stable_id) → fidelity_level='minimal', compact_flag=True."""
    classified = ClassifiedResult(
        kind=OutcomeKind.RENDERABLE_SKILL,
        normalized=_full_normalized(
            visible_title=None,
            path=None,
            source=None,
            description=None,
        ),
        reason="minimal trusted fields",
        authority_state="degraded",
    )

    vm = build_view_model(classified)

    assert vm is not None
    assert vm.authority_state == "degraded"
    assert vm.fidelity_level == "minimal"
    assert vm.compact_flag is True


# --- Task 3.8: select_renderer routes to plain (UX-004) ---


def test_select_renderer_routes_to_plain():
    """is_tty=False → plain renderer, uses card.name/card.relevance."""
    from scripts.skill_hub_runtime_ux import RuntimeSkillCard

    vm = RuntimeSkillCard(
        id="test", name="Test Skill", path="/x", source="src",
        description="desc", authority_state="healthy", relevance=0.9,
    )
    plan = RenderPlan(
        outcome_kind=OutcomeKind.RENDERABLE_SKILL,
        exit_code=0,
        cards=[vm],
        message="",
        classified_results=[],
    )

    from scripts.skill_hub_cards_core import _select_renderer
    output = _select_renderer(plan, use_json=False, style="plain", is_tty=False)

    # Plain renderer should use card.name
    assert "Test Skill" in output
    assert "read /x" in output


# --- Task 3.9: select_renderer routes to rich (UX-005) ---


def test_select_renderer_routes_to_rich():
    """is_tty=True + style='rich' → rich renderer, uses card.name/card.relevance."""
    from scripts.skill_hub_runtime_ux import RuntimeSkillCard

    vm = RuntimeSkillCard(
        id="test", name="Rich Skill", path="/y", source="src",
        description="rich desc", authority_state="healthy", relevance=0.7,
    )
    plan = RenderPlan(
        outcome_kind=OutcomeKind.RENDERABLE_SKILL,
        exit_code=0,
        cards=[vm],
        message="",
        classified_results=[],
    )

    from scripts.skill_hub_cards_core import _select_renderer
    output = _select_renderer(plan, use_json=False, style="rich", is_tty=True)

    # Rich renderer uses card.name
    assert "Rich Skill" in output


def test_cli_cards_output_includes_plain_intro_before_rendered_cards(monkeypatch, capsys):
    """Cards CLI emits governed intro/banner before card output in non-JSON mode."""
    from scripts import skill_hub_cards_core as mod

    raw_search_output = '{"hits":[{"ref":"skill:python-patterns:abc","score":0.9}]}'
    chunk_texts = {
        "skill:python-patterns:abc": "\n".join(
            [
                "read /skills/python-patterns/SKILL.md",
                "Source: claude-skills",
                "Use when you need Python idioms.",
            ]
        )
    }

    monkeypatch.setattr(mod, "_load_search_payload", lambda args, *, segment_path=None: raw_search_output)
    monkeypatch.setattr(mod, "run_get", lambda refs, *, segment_path=None: chunk_texts)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    exit_code = mod.cli(["python", "--limit", "1"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.startswith("=== Skill Hub ===")
    assert "sentence query" in output
    assert "# Skill: python-patterns" in output
    assert output.index("=== Skill Hub ===") < output.index("# Skill: python-patterns")


def test_cli_cards_output_includes_rich_banner_before_rendered_cards(monkeypatch, capsys):
    """TTY rich cards CLI emits governed hero banner before rich card output."""
    from scripts import skill_hub_cards_core as mod

    raw_search_output = '{"hits":[{"ref":"skill:python-patterns:abc","score":0.9}]}'
    chunk_texts = {
        "skill:python-patterns:abc": "\n".join(
            [
                "read /skills/python-patterns/SKILL.md",
                "Source: claude-skills",
                "Use when you need Python idioms.",
            ]
        )
    }

    monkeypatch.setattr(mod, "_load_search_payload", lambda args, *, segment_path=None: raw_search_output)
    monkeypatch.setattr(mod, "run_get", lambda refs, *, segment_path=None: chunk_texts)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    exit_code = mod.cli(["python", "--limit", "1", "--style", "rich"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "███████╗██╗  ██╗██╗██╗     ██╗     ███████╗" in output
    assert "sentence query" in output
    assert "python-patterns" in output
    assert output.index("███████╗") < output.index("python-patterns")


def test_cli_json_output_does_not_include_intro(monkeypatch, capsys):
    """JSON mode remains machine-readable: no intro/banner prefix."""
    from scripts import skill_hub_cards_core as mod

    raw_search_output = '{"hits":[{"ref":"skill:python-patterns:abc","score":0.9}]}'
    chunk_texts = {
        "skill:python-patterns:abc": "\n".join(
            [
                "read /skills/python-patterns/SKILL.md",
                "Source: claude-skills",
                "Use when you need Python idioms.",
            ]
        )
    }

    monkeypatch.setattr(mod, "_load_search_payload", lambda args, *, segment_path=None: raw_search_output)
    monkeypatch.setattr(mod, "run_get", lambda refs, *, segment_path=None: chunk_texts)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    exit_code = mod.cli(["python", "--limit", "1", "--json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert not output.startswith("=== Skill Hub ===")
    assert "███████╗" not in output
    assert output.lstrip().startswith("{")


def test_managed_skill_excerpt_promotes_generic_description_to_healthy_card():
    """Managed skill excerpts use the first human content line as card description."""
    from scripts.skill_hub_cards_core import build_render_plan

    raw_search_output = '{"hits":[{"ref":"skill:e2e-testing:d8734a8f04","score":5.23}]}'
    chunk_texts = {
        "skill:e2e-testing:d8734a8f04": "\n".join(
            [
                "## [skill:e2e-testing:d8734a8f04] e2e-testing.md",
                "<!-- managed-by:indexing-skills-safely:start -->",
                "read /Users/example/.claude/skills/e2e-testing/SKILL.md",
                "# Skill: e2e-testing",
                "**Source**: claude-skills",
                "Playwright E2E testing patterns, Page Object Model, CI integration, and flaky test strategies.",
                "<!-- managed-by:indexing-skills-safely:end -->",
            ]
        )
    }

    plan = build_render_plan(raw_search_output, chunk_texts)

    assert plan.cards[0].authority_state == "healthy"
    assert plan.cards[0].fidelity_level == "full"
    assert plan.cards[0].description.startswith("Playwright E2E testing patterns")


def test_cli_cards_rejects_whitespace_query_without_search(monkeypatch, capsys):
    """Cards mode matches plain search validation for whitespace-only queries."""
    from scripts import skill_hub_cards_core as mod

    def fail_search(*args, **kwargs):
        raise AssertionError("whitespace-only query must not execute search")

    monkeypatch.setattr(mod, "_load_search_payload", fail_search)

    exit_code = mod.cli(["   ", "--limit", "1"])

    assert exit_code == 4
    assert "Query rejected: Query cannot be empty or whitespace-only" in capsys.readouterr().err
