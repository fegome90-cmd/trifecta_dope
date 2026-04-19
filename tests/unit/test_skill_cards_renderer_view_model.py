import io
import re

from src.application.skill_card_view_model import SkillCardViewModel
from src.cli.skill_cards import render_card


def test_render_rich_healthy_has_no_badge():
    card = SkillCardViewModel(
        id="test1",
        name="Test 1",
        path="/some/path",
        source="agent",
        description="desc",
        authority_state="healthy"
    )
    output = io.StringIO()
    render_card(card, style="rich", file=output)
    text = output.getvalue()
    assert "[DEGRADED]" not in text


def test_render_rich_degraded_has_badge():
    card = SkillCardViewModel(
        id="test1",
        name="Test 1",
        path="/some/path",
        source="agent",
        description="desc",
        authority_state="degraded"
    )
    output = io.StringIO()
    render_card(card, style="rich", file=output)
    text = output.getvalue()
    # Note: Rich might render ANSI depending on the console but we test that the raw string has the text characters
    assert "[DEGRADED]" in text


def test_render_compact_degraded_has_marker():
    card = SkillCardViewModel(
        id="test1",
        name="Test 1",
        path="/some/path",
        source="agent",
        description="desc",
        authority_state="degraded"
    )
    output = io.StringIO()
    # It logs to console, but we capture printed output to fake file
    render_card(card, style="compact", file=output)
    text = output.getvalue()
    assert "[DEGRADED]" in text


def test_render_plain_degraded_exact_string():
    card = SkillCardViewModel(
        id="test1",
        name="Test 1",
        path="/some/path",
        source="agent",
        description="desc",
        authority_state="degraded"
    )
    output = io.StringIO()
    render_card(card, style="plain", file=output)
    text = output.getvalue()
    assert "Status: DEGRADED" in text
    
def test_render_plain_degraded_no_ansi():
    card = SkillCardViewModel(
        id="test1",
        name="Test 1",
        path="/some/path",
        source="agent",
        description="desc",
        authority_state="degraded"
    )
    output = io.StringIO()
    render_card(card, style="plain", file=output)
    text = output.getvalue()
    # simple check for CSI sequences \x1b[
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    assert not ansi_escape.search(text)
    assert "Status: DEGRADED" in text
