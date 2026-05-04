from __future__ import annotations

import io

from scripts.skill_hub_runtime_ux import (
    ANSI_BRIGHT_WHITE,
    ANSI_RESET,
    SKILL_HUB_HERO_BANNER,
    SKILL_HUB_INTRO_BANNER,
    SKILL_HUB_SENTENCE_GUIDANCE,
    emit_intro,
    render_intro,
)


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


class PipeBuffer(io.StringIO):
    def isatty(self) -> bool:
        return False


def test_render_intro_plain_fallback_stays_compact() -> None:
    intro = render_intro(query_hint="sql data base", rich=False)

    assert SKILL_HUB_INTRO_BANNER in intro
    assert SKILL_HUB_SENTENCE_GUIDANCE in intro
    assert "Query: sql data base" in intro
    assert "███████" not in intro



def test_render_intro_rich_uses_hero_banner_lines() -> None:
    intro = render_intro(query_hint="sql data base", rich=True, colorize=True)

    for line in SKILL_HUB_HERO_BANNER:
        assert f"{ANSI_BRIGHT_WHITE}{line}{ANSI_RESET}" in intro
    assert SKILL_HUB_SENTENCE_GUIDANCE in intro
    assert "Query: sql data base" in intro



def test_emit_intro_uses_hero_banner_for_tty(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    buffer = TtyBuffer()

    emit_intro(query_hint="sql data base", file=buffer)

    output = buffer.getvalue()
    assert "███████" in output
    assert ANSI_BRIGHT_WHITE in output
    assert SKILL_HUB_SENTENCE_GUIDANCE in output


def test_emit_intro_uses_hero_banner_without_color_when_no_color_is_set(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    buffer = TtyBuffer()

    emit_intro(query_hint="sql data base", file=buffer)

    output = buffer.getvalue()
    assert "███████" in output
    assert ANSI_BRIGHT_WHITE not in output
    assert ANSI_RESET not in output


def test_emit_intro_uses_plain_fallback_for_non_tty(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    buffer = PipeBuffer()

    emit_intro(query_hint="sql data base", file=buffer)

    output = buffer.getvalue()
    assert SKILL_HUB_INTRO_BANNER in output
    assert "███████" not in output
    assert ANSI_BRIGHT_WHITE not in output


# --- Task 4.3: Only two intro variants, no render_intro outside runtime_ux ---


def test_render_intro_only_two_variants() -> None:
    """UX-008: render_intro output matches exactly one of two contracts."""
    plain = render_intro(rich=False)
    rich_output = render_intro(rich=True)

    assert SKILL_HUB_INTRO_BANNER in plain
    assert SKILL_HUB_SENTENCE_GUIDANCE in plain
    assert "███████" not in plain

    assert any(line in rich_output for line in SKILL_HUB_HERO_BANNER)
    assert SKILL_HUB_SENTENCE_GUIDANCE in rich_output
