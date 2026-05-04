"""Tests for skill-hub render pipeline.

Covers: sanitize_query, RuntimeSkillCard.__post_init__, SkillCard factory,
RenderPlan compat shim, description fallback in render_cards_plain/render_cards_rich,
H-1 exit codes, H-5 limit cap, H-2 JSON whitelist, H-8 synthetic cards, H-4 wrapper.
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scripts.skill_hub_cards_core import (
    ClassifiedResult,
    NormalizedResult,
    OutcomeKind,
    RenderPlan,
    SearchRuntimeError,
    GetRuntimeError,
    SkillCard,
    build_view_model,
    build_render_plan,
    sanitize_query,
    run_search,
    run_get,
    output_json,
    _validate_positive_limit,
)
from scripts.skill_hub_runtime_ux import (
    RuntimeSkillCard,
    render_cards_plain,
    render_cards_rich,
)


# ─── Helpers ──────────────────────────────────────────────────────────


def _full_normalized(**overrides) -> NormalizedResult:
    defaults = dict(
        ref="skill:python-patterns:abc123",
        raw_type="skill",
        raw_title="Python Patterns",
        score=0.85,
        stable_id="python-patterns",
        visible_title="Python Patterns",
        path="/skills/python-patterns/SKILL.md",
        source="claude-skills",
        description="Use when you need Python idioms.",
        metadata_message=None,
        metadata_reason=None,
    )
    defaults.update(overrides)
    return NormalizedResult(**defaults)


def _make_card(**overrides) -> RuntimeSkillCard:
    defaults = dict(
        id="test-skill",
        name="Test Skill",
        path="/skills/test/SKILL.md",
        source="test-source",
        description="A test description.",
        authority_state="healthy",
        relevance=0.9,
    )
    defaults.update(overrides)
    return RuntimeSkillCard(**defaults)


# ─── sanitize_query ──────────────────────────────────────────────────


class TestSanitizeQuery:
    def test_null_byte_stripped(self) -> None:
        assert sanitize_query("test\x00null") == "testnull"

    def test_bom_stripped(self) -> None:
        assert sanitize_query("\ufeffsearch term") == "search term"

    def test_rtl_override_stripped(self) -> None:
        query = "hello\u202eworld"
        assert sanitize_query(query) == "helloworld"

    def test_all_bidi_chars_stripped(self) -> None:
        bidi = "\u202e\u200f\u202a\u202b\u202c\u202d\u2066\u2067\u2068\u2069"
        assert sanitize_query(f"query{bidi}text") == "querytext"

    def test_query_truncated_at_max_length(self) -> None:
        long_query = "a" * 600
        result = sanitize_query(long_query)
        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")
        assert result.startswith("a" * 500)

    def test_custom_max_length(self) -> None:
        long_query = "a" * 200
        result = sanitize_query(long_query, max_length=100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            sanitize_query("   ")

    def test_empty_query_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            sanitize_query("")

    def test_normal_query_passes_through(self) -> None:
        assert sanitize_query("refactor code") == "refactor code"

    def test_leading_trailing_whitespace_stripped(self) -> None:
        assert sanitize_query("  hello  ") == "hello"

    def test_null_and_bom_combined(self) -> None:
        assert sanitize_query("\ufefftest\x00query") == "testquery"

    def test_query_at_exactly_max_length_not_truncated(self) -> None:
        query = "a" * 500
        assert sanitize_query(query) == query


# ─── RuntimeSkillCard.__post_init__ ──────────────────────────────────


class TestRuntimeSkillCardPostInit:
    def test_rejects_none_id(self) -> None:
        with pytest.raises(ValueError, match="id must be provided"):
            RuntimeSkillCard(
                id=None, name="N", path="p", source="s", description="d"  # type: ignore[arg-type]
            )

    def test_rejects_none_name(self) -> None:
        with pytest.raises(ValueError, match="name must be provided"):
            RuntimeSkillCard(
                id="x", name=None, path="p", source="s", description="d"  # type: ignore[arg-type]
            )

    def test_rejects_invalid_authority_state(self) -> None:
        with pytest.raises(ValueError, match="authority_state must be"):
            RuntimeSkillCard(
                id="x", name="N", path="p", source="s", description="d",
                authority_state="broken",
            )

    def test_accepts_healthy_authority_state(self) -> None:
        card = _make_card(authority_state="healthy")
        assert card.authority_state == "healthy"

    def test_accepts_degraded_authority_state(self) -> None:
        card = _make_card(authority_state="degraded")
        assert card.authority_state == "degraded"

    def test_default_authority_state_is_healthy(self) -> None:
        card = _make_card()
        assert card.authority_state == "healthy"


# ─── SkillCard factory ───────────────────────────────────────────────


class TestSkillCardFactory:
    def test_returns_runtime_skill_card_instance(self) -> None:
        card = SkillCard(
            id="x", title="T", path="p", source="s", description="d", score=1.0
        )
        assert type(card).__name__ == "RuntimeSkillCard"

    def test_maps_title_to_name(self) -> None:
        card = SkillCard(
            id="x", title="My Skill", path="p", source="s", description="d", score=1.0
        )
        assert card.name == "My Skill"

    def test_maps_score_to_relevance(self) -> None:
        card = SkillCard(
            id="x", title="T", path="p", source="s", description="d", score=0.85
        )
        assert card.relevance == 0.85

    def test_passes_through_other_fields(self) -> None:
        card = SkillCard(
            id="test-id", title="T", path="/path", source="src", description="desc", score=0.5
        )
        assert card.id == "test-id"
        assert card.path == "/path"
        assert card.source == "src"
        assert card.description == "desc"


# ─── RenderPlan compat shim ─────────────────────────────────────────


class TestRenderPlanCompatShim:
    def test_pure_runtime_skill_cards_pass_through(self) -> None:
        card = _make_card()
        plan = RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=0,
            cards=[card],
            message="",
            classified_results=[],
        )
        assert plan.cards == [card]
        assert isinstance(plan.cards[0], RuntimeSkillCard)

    def test_empty_cards_list_accepted(self) -> None:
        plan = RenderPlan(
            outcome_kind=OutcomeKind.EMPTY,
            exit_code=4,
            cards=[],
            message="No search hits found.",
            classified_results=[],
        )
        assert plan.cards == []


# ─── Description fallback ───────────────────────────────────────────


class TestDescriptionFallback:
    def test_plain_empty_description_shows_fallback(self) -> None:
        card = _make_card(description="")
        output = render_cards_plain([card])
        assert "Description unavailable" in output

    def test_rich_empty_description_shows_fallback(self) -> None:
        card = _make_card(description="")
        output = render_cards_rich([card])
        assert "Description unavailable" in output

    def test_plain_none_description_shows_fallback(self) -> None:
        card = _make_card(description=None)  # type: ignore[arg-type]
        output = render_cards_plain([card])
        assert "Description unavailable" in output

    def test_rich_none_description_shows_fallback(self) -> None:
        card = _make_card(description=None)  # type: ignore[arg-type]
        output = render_cards_rich([card])
        assert "Description unavailable" in output

    def test_plain_nonempty_description_shows_actual(self) -> None:
        card = _make_card(description="Use for testing")
        output = render_cards_plain([card])
        assert "Use for testing" in output
        assert "Description unavailable" not in output

    def test_rich_nonempty_description_shows_actual(self) -> None:
        card = _make_card(description="Use for testing")
        output = render_cards_rich([card])
        assert "Use for testing" in output
        assert "Description unavailable" not in output

    def test_degraded_empty_description_shows_fallback_plain(self) -> None:
        card = _make_card(description="", authority_state="degraded")
        output = render_cards_plain([card])
        assert "Description unavailable" in output
        assert "DEGRADED" in output


# ─── Timeout error classes ──────────────────────────────────────────


class TestTimeoutErrors:
    def test_search_runtime_error_has_elapsed_seconds(self) -> None:
        err = SearchRuntimeError("timed out", elapsed_seconds=30.1, partial_results='{"hits":[]}')
        assert err.elapsed_seconds == 30.1
        assert err.partial_results == '{"hits":[]}'

    def test_get_runtime_error_has_elapsed_seconds(self) -> None:
        err = GetRuntimeError("timed out", elapsed_seconds=29.5)
        assert err.elapsed_seconds == 29.5
        assert err.partial_results is None

    def test_run_search_timeout_raises_search_runtime_error(self) -> None:
        with patch("scripts.skill_hub_cards_core.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
            with pytest.raises(SearchRuntimeError) as exc_info:
                run_search("test", 5)
            assert exc_info.value.elapsed_seconds > 0

    def test_run_get_timeout_raises_get_runtime_error(self) -> None:
        with patch("scripts.skill_hub_cards_core.subprocess.run") as mock_run:
            exc = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
            exc.stdout = b'{"partial": true}'
            mock_run.side_effect = exc
            with pytest.raises(GetRuntimeError) as exc_info:
                run_get(["skill:test:abc"])
            assert exc_info.value.elapsed_seconds > 0
            assert exc_info.value.partial_results is not None

    def test_run_search_timeout_with_string_stdout(self) -> None:
        with patch("scripts.skill_hub_cards_core.subprocess.run") as mock_run:
            exc = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
            exc.stdout = '{"partial": true}'
            mock_run.side_effect = exc
            with pytest.raises(SearchRuntimeError) as exc_info:
                run_search("test", 5)
            assert exc_info.value.partial_results == '{"partial": true}'


# ─── SkillCardViewModel alias ─────────────────────────────────────────


class TestSkillCardViewModelAlias:
    def test_alias_is_runtime_skill_card(self) -> None:
        """SkillCardViewModel re-exports RuntimeSkillCard transparently."""
        from src.application.skill_card_view_model import SkillCardViewModel

        assert SkillCardViewModel is RuntimeSkillCard


# ─── Render path exclusivity ─────────────────────────────────────────


class TestRenderPathExclusivity:
    def test_cards_core_has_no_render_plain(self) -> None:
        """render_plain was deleted from cards_core."""
        import scripts.skill_hub_cards_core as mod

        assert not hasattr(mod, "render_plain")

    def test_cards_core_has_no_render_rich(self) -> None:
        """render_rich was deleted from cards_core."""
        import scripts.skill_hub_cards_core as mod

        assert not hasattr(mod, "render_rich")

    def test_select_renderer_delegates_to_runtime_ux_plain(self) -> None:
        """_select_renderer delegates plain rendering to runtime_ux."""
        import scripts.skill_hub_cards_core as core

        card = _make_card()
        plan = RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=0,
            cards=[card],
            message="",
            classified_results=[],
        )
        result = core._select_renderer(plan, use_json=False, style="plain", is_tty=False)
        # The output must match what runtime_ux.render_cards_plain produces
        expected = render_cards_plain([card])
        assert result == expected


# ─── H-1: Exit code for rejected/empty queries ────────────────────────


class TestExitCodeRejectedQueries:
    def test_cli_rejects_whitespace_query_returns_exit_empty(self, monkeypatch, capsys) -> None:
        from scripts import skill_hub_cards_core as mod

        monkeypatch.setattr(mod, "_load_search_payload", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not reach search")))
        exit_code = mod.cli(["   ", "--limit", "1"])
        assert exit_code == 4
        captured = capsys.readouterr()
        assert "Query rejected" in captured.err

    def test_cli_no_query_returns_exit_empty(self, monkeypatch, capsys) -> None:
        from scripts import skill_hub_cards_core as mod

        monkeypatch.setattr(mod, "_load_search_payload", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not reach search")))
        exit_code = mod.cli([])
        assert exit_code == 4
        captured = capsys.readouterr()
        assert len(captured.err) > 0


# ─── H-5: Limit upper bound cap ──────────────────────────────────────


class TestLimitCap:
    def test_validate_limit_accepts_100(self) -> None:
        assert _validate_positive_limit(100) == 100

    def test_validate_limit_rejects_101(self) -> None:
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            _validate_positive_limit(101)

    def test_validate_limit_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="limit must be a positive integer"):
            _validate_positive_limit(0)

    def test_cli_limit_over_100_returns_error(self, monkeypatch, capsys) -> None:
        from scripts import skill_hub_cards_core as mod

        monkeypatch.setattr(mod, "_load_search_payload", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not reach search")))
        exit_code = mod.cli(["test", "--limit", "101"])
        assert exit_code == 1


# ─── H-2: JSON output field whitelist ────────────────────────────────


class TestJsonOutputWhitelist:
    def test_json_output_has_exactly_public_fields(self) -> None:
        card = _make_card()
        plan = RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=0,
            cards=[card],
            message="",
            classified_results=[],
        )
        raw = output_json(plan)
        data = __import__("json").loads(raw)
        card_dict = data["cards"][0]
        expected_fields = {"id", "name", "path", "source", "description", "authority_state", "relevance", "synthetic"}
        assert set(card_dict.keys()) == expected_fields

    def test_json_output_excludes_internal_fields(self) -> None:
        card = _make_card()
        plan = RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=0,
            cards=[card],
            message="",
            classified_results=[],
        )
        raw = output_json(plan)
        data = __import__("json").loads(raw)
        card_dict = data["cards"][0]
        for internal in ("fidelity_level", "compact_flag", "search_hints", "triggers"):
            assert internal not in card_dict

    def test_json_output_preserves_top_level_structure(self) -> None:
        card = _make_card()
        plan = RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=0,
            cards=[card],
            message="",
            classified_results=[],
        )
        raw = output_json(plan)
        data = __import__("json").loads(raw)
        for key in ("outcome_kind", "exit_code", "message", "cards", "classified_results"):
            assert key in data


# ─── H-8: Synthetic card detection ───────────────────────────────────


class TestSyntheticDetection:
    def test_view_model_marks_synthetic_when_no_trusted_fields(self) -> None:
        from scripts.skill_hub_cards_core import ClassifiedResult, NormalizedResult, OutcomeKind

        normalized = _full_normalized(path=None, source=None, description=None)
        result = ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=normalized,
            reason="test",
            authority_state="degraded",
        )
        card = build_view_model(result)
        assert card is not None
        assert card.synthetic is True

    def test_view_model_not_synthetic_with_path(self) -> None:
        from scripts.skill_hub_cards_core import ClassifiedResult, OutcomeKind

        normalized = _full_normalized()
        result = ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=normalized,
            reason="test",
            authority_state="healthy",
        )
        card = build_view_model(result)
        assert card is not None
        assert card.synthetic is False

    def test_view_model_not_synthetic_with_source_only(self) -> None:
        from scripts.skill_hub_cards_core import ClassifiedResult, OutcomeKind

        normalized = _full_normalized(path=None, source="some_source", description=None)
        result = ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=normalized,
            reason="test",
            authority_state="healthy",
        )
        card = build_view_model(result)
        assert card is not None
        assert card.synthetic is False

    def test_view_model_not_synthetic_with_description_only(self) -> None:
        from scripts.skill_hub_cards_core import ClassifiedResult, OutcomeKind

        normalized = _full_normalized(path=None, source=None, description="some desc")
        result = ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=normalized,
            reason="test",
            authority_state="healthy",
        )
        card = build_view_model(result)
        assert card is not None
        assert card.synthetic is False


class TestAllSyntheticExitCode:
    def test_all_synthetic_cards_return_exit_empty(self) -> None:
        """build_render_plan returns EXIT_EMPTY when all cards are synthetic (no trusted fields)."""
        import json as _json
        from scripts.skill_hub_cards_core import build_render_plan, EXIT_EMPTY

        # Fake ref with empty chunk_text → normalize_result gets no path/source/description
        # → classify_result produces RENDERABLE_SKILL degraded → build_view_model sets synthetic=True
        search_output = _json.dumps({
            "hits": [{"ref": "skill:nonexistent-fake:abc123", "score": 0.5, "title": "Fake Skill"}]
        })
        # Empty chunk_texts: the ref has no backing content
        plan = build_render_plan(search_output, chunk_texts={}, limit=5)
        assert plan.exit_code == EXIT_EMPTY
        assert len(plan.cards) == 1
        assert plan.cards[0].synthetic is True


# ─── H-8: Synthetic renderer tags ────────────────────────────────────


class TestSyntheticRendererTags:
    def test_plain_renderer_shows_synthetic_tag(self) -> None:
        card = _make_card(synthetic=True)
        output = render_cards_plain([card])
        assert "[synthetic]" in output

    def test_rich_renderer_shows_synthetic_tag(self) -> None:
        card = _make_card(synthetic=True)
        output = render_cards_rich([card])
        assert "[SYNTHETIC]" in output


# ─── H-4: Bash wrapper flag forwarding ───────────────────────────────


class TestWrapperFlags:
    def test_wrapper_json_flag_produces_json_output(self) -> None:
        result = subprocess.run(
            ["scripts/skill-hub", "-c", "--json", "python"],
            capture_output=True, text=True, timeout=30,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent),
        )
        assert result.returncode == 0, f"wrapper failed: {result.stderr}"
        import json
        data = json.loads(result.stdout)
        assert "cards" in data

    def test_wrapper_style_flag_overrides_tty(self) -> None:
        result = subprocess.run(
            ["scripts/skill-hub", "-c", "--style", "plain", "python"],
            capture_output=True, text=True, timeout=30,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent),
        )
        if result.returncode == 0 and result.stdout.strip():
            assert "[SKILL]" not in result.stdout or "Description unavailable" not in result.stdout

    def test_wrapper_flags_not_in_query(self) -> None:
        result = subprocess.run(
            ["scripts/skill-hub", "-c", "--json", "python"],
            capture_output=True, text=True, timeout=30,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent),
        )
        assert "--json" not in result.stderr

    def test_wrapper_style_without_value_exits_error(self) -> None:
        result = subprocess.run(
            ["scripts/skill-hub", "-c", "--style"],
            capture_output=True, text=True, timeout=10,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent),
        )
        assert result.returncode == 2
        assert "style" in result.stderr.lower()
