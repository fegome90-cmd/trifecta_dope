"""Test PROMPT_FIX_HINT in generated stubs."""

from pathlib import Path
import tempfile
from src.application.stub_regen_use_case import StubRegenUseCase


def test_repo_map_contains_prompt_fix_hint():
    """Test that repo_map.md contains PROMPT_FIX_HINT."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create minimal segment structure
        (tmpdir / "src").mkdir()

        # Execute stub regeneration
        use_case = StubRegenUseCase()
        result = use_case.execute(tmpdir)

        # Verify success
        assert result["regen_ok"]
        assert "repo_map.md" in result["stubs"]

        # Read generated file
        repo_map = (tmpdir / "_ctx" / "generated" / "repo_map.md").read_text()

        # Verify PROMPT_FIX_HINT present
        assert "PROMPT_FIX_HINT" in repo_map
        assert "copy NEXT_STEPS and rerun" in repo_map


def test_symbols_stub_contains_prompt_fix_hint():
    """Test that symbols_stub.md contains PROMPT_FIX_HINT."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create minimal segment structure
        (tmpdir / "src").mkdir()

        # Execute stub regeneration
        use_case = StubRegenUseCase()
        result = use_case.execute(tmpdir)

        # Verify success
        assert result["regen_ok"]
        assert "symbols_stub.md" in result["stubs"]

        # Read generated file
        symbols_stub = (tmpdir / "_ctx" / "generated" / "symbols_stub.md").read_text()

        # Verify PROMPT_FIX_HINT present
        assert "PROMPT_FIX_HINT" in symbols_stub
        assert "copy NEXT_STEPS and rerun" in symbols_stub
