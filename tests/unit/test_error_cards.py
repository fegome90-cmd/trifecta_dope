"""Unit tests for error_cards.py module."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.cli.error_cards import render_error_card


def test_render_error_card_stable_markers():
    """Verify all stable markers are present for grep assertions."""
    card = render_error_card(
        error_code="TEST_CODE",
        error_class="TEST_CLASS",
        cause="Test cause",
        next_steps=["Step 1", "Step 2"],
        verify_cmd="test --cmd",
    )
    assert "TRIFECTA_ERROR_CODE: TEST_CODE" in card
    assert "CLASS: TEST_CLASS" in card
    assert "NEXT_STEPS:" in card
    assert "VERIFY:" in card


def test_render_error_card_empty_next_steps():
    """Verify empty next_steps list doesn't crash."""
    card = render_error_card(
        error_code="CODE",
        error_class="CLASS",
        cause="Cause",
        next_steps=[],
        verify_cmd="cmd",
    )
    assert "TRIFECTA_ERROR_CODE: CODE" in card


def test_render_error_card_unicode():
    """Verify Unicode in error messages works."""
    card = render_error_card(
        error_code="UNICODE_TEST",
        error_class="VALIDATION",
        cause="Error: ñoño 友達 🎉",
        next_steps=["Fix the ñ"],
        verify_cmd="test",
    )
    assert "ñoño" in card
