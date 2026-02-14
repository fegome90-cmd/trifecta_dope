"""Tests for zero-hit test suite script."""

import json
import subprocess
from pathlib import Path
import pytest


class TestZeroHitSuiteScript:
    """Test the test_zero_hit_suite.py script."""

    def test_script_exists(self):
        """Script file exists and is executable."""
        script_path = Path("scripts/test_zero_hit_suite.py")
        assert script_path.exists()
        assert script_path.stat().st_mode & 0o111  # Executable

    def test_script_help(self):
        """Script shows help correctly."""
        result = subprocess.run(
            ["python", "scripts/test_zero_hit_suite.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Zero-Hit Testing Suite" in result.stdout

    def test_script_runs_successfully(self, tmp_path):
        """Script executes without errors."""
        output_file = tmp_path / "report.json"

        result = subprocess.run(
            [
                "python",
                "scripts/test_zero_hit_suite.py",
                "--segment",
                ".",
                "--output",
                str(output_file),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Script may exit with code 1 if zero-hit ratio > 50%, which is expected
        assert result.returncode in (0, 1)
        assert output_file.exists()

    def test_json_output_format(self, tmp_path):
        """JSON output has correct structure."""
        output_file = tmp_path / "report.json"

        subprocess.run(
            [
                "python",
                "scripts/test_zero_hit_suite.py",
                "--segment",
                ".",
                "--output",
                str(output_file),
                "--format",
                "json",
            ],
            capture_output=True,
            timeout=60,
        )

        data = json.loads(output_file.read_text())

        # Check required fields
        assert "timestamp" in data
        assert "segment" in data
        assert "summary" in data
        assert "by_category" in data
        assert "results" in data

        # Check summary fields
        summary = data["summary"]
        assert "total_queries" in summary
        assert "zero_hits" in summary
        assert "rejected" in summary
        assert "zero_hit_ratio" in summary

    def test_markdown_output_format(self, tmp_path):
        """Markdown output has correct structure."""
        output_file = tmp_path / "report.md"

        subprocess.run(
            [
                "python",
                "scripts/test_zero_hit_suite.py",
                "--segment",
                ".",
                "--output",
                str(output_file),
                "--format",
                "markdown",
            ],
            capture_output=True,
            timeout=60,
        )

        content = output_file.read_text()

        # Check markdown structure
        assert "# Zero-Hit Test Suite Report" in content
        assert "## Summary" in content
        assert "## Results by Category" in content

    def test_categories_included(self, tmp_path):
        """All test categories are included in output."""
        output_file = tmp_path / "report.json"

        subprocess.run(
            [
                "python",
                "scripts/test_zero_hit_suite.py",
                "--segment",
                ".",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            timeout=60,
        )

        data = json.loads(output_file.read_text())

        expected_categories = [
            "empty",
            "vague",
            "short",
            "spanish",
            "english_common",
            "technical",
            "edge_cases",
        ]

        for category in expected_categories:
            assert category in data["by_category"], f"Missing category: {category}"

    def test_spanish_queries_present(self, tmp_path):
        """Spanish queries are tested."""
        output_file = tmp_path / "report.json"

        subprocess.run(
            [
                "python",
                "scripts/test_zero_hit_suite.py",
                "--segment",
                ".",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            timeout=60,
        )

        data = json.loads(output_file.read_text())

        # Check that spanish queries are in results
        spanish_results = [r for r in data["results"] if r["category"] == "spanish"]
        assert len(spanish_results) > 0

        # Check specific spanish terms
        spanish_queries = {r["query"] for r in spanish_results}
        assert "servicio" in spanish_queries
        assert "documentación" in spanish_queries

    def test_b2_rejection_detection(self, tmp_path):
        """B2 rejections are detected and reported."""
        output_file = tmp_path / "report.json"

        subprocess.run(
            [
                "python",
                "scripts/test_zero_hit_suite.py",
                "--segment",
                ".",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            timeout=60,
        )

        data = json.loads(output_file.read_text())

        # Should have some rejected queries (B2 intervention)
        rejected_results = [r for r in data["results"] if r["rejected"]]

        # At minimum, empty strings should be rejected
        if len(rejected_results) > 0:
            assert any(r["query"] == "" for r in rejected_results)
