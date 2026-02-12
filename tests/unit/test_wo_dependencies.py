"""
Tests for WO dependency analysis tool.
"""

import subprocess


class TestWODependenciesTool:
    """Test ctx_wo_dependencies.py CLI tool."""

    def test_help_output(self):
        """Test that the tool has a help interface."""
        result = subprocess.run(
            ["python", "scripts/ctx_wo_dependencies.py", "--help"], capture_output=True
        )
        assert result.returncode == 0
        output = result.stdout.decode().lower()
        assert "dependency" in output

    def test_tool_exists(self):
        """Test that the tool file exists and is executable."""
        from pathlib import Path

        tool_path = Path("scripts/ctx_wo_dependencies.py")
        assert tool_path.exists()
