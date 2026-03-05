"""Integration tests for --explain JSON contract in ctx search."""
import json
import subprocess
from pathlib import Path


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """Run trifecta CLI and return exit code, stdout, stderr."""
    result = subprocess.run(
        ["uv", "run", "trifecta"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


class TestSearchExplainJsonContract:
    """Tests for --explain JSON output contract."""

    def test_explain_returns_valid_json(self):
        """Verify --explain returns valid JSON."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "test",
            "--segment", ".",
            "--limit", "1",
            "--explain"
        ])
        assert code == 0
        # Should parse as valid JSON
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_explain_has_required_top_level_keys(self):
        """Verify JSON has all required top-level keys."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "test",
            "--segment", ".",
            "--limit", "1",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        required_keys = ["query", "normalized_query", "linter", "expansions", "hits", "total_hits"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    def test_explain_linter_structure(self):
        """Verify linter object has correct structure."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "test",
            "--segment", ".",
            "--limit", "1",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        linter = data["linter"]
        assert "class" in linter
        assert "expanded" in linter
        assert "added_strong" in linter
        assert "added_weak" in linter
        assert isinstance(linter["expanded"], bool)
        assert isinstance(linter["added_strong"], list)
        assert isinstance(linter["added_weak"], list)

    def test_explain_expansions_structure(self):
        """Verify expansions object has correct structure."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "test",
            "--segment", ".",
            "--limit", "1",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        expansions = data["expansions"]
        assert "alias_expanded" in expansions
        assert "alias_terms_count" in expansions
        assert "expanded_terms" in expansions
        assert isinstance(expansions["alias_expanded"], bool)
        assert isinstance(expansions["alias_terms_count"], int)
        assert isinstance(expansions["expanded_terms"], list)

    def test_explain_hits_structure(self):
        """Verify each hit has correct structure."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "TDD",
            "--segment", ".",
            "--limit", "2",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        assert data["total_hits"] == len(data["hits"])

        for hit in data["hits"]:
            assert "ref" in hit, "Hit missing 'ref'"
            assert "score" in hit, "Hit missing 'score'"
            assert "tokens_est" in hit, "Hit missing 'tokens_est'"
            assert "signals" in hit, "Hit missing 'signals'"
            assert "matched_terms" in hit["signals"], "Hit signals missing 'matched_terms'"

            # Type checks
            assert isinstance(hit["ref"], str)
            assert isinstance(hit["score"], (int, float))
            assert isinstance(hit["tokens_est"], int)
            assert isinstance(hit["signals"]["matched_terms"], list)

    def test_explain_text_format(self):
        """Verify --explain-format text works."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "test",
            "--segment", ".",
            "--limit", "1",
            "--explain",
            "--explain-format", "text"
        ])
        assert code == 0
        # Should NOT be JSON
        assert not out.strip().startswith("{")
        # Should have key markers
        assert "Search Explanation" in out or "Hits" in out

    def test_explain_query_is_preserved(self):
        """Verify original query is preserved in output."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "TDD Workflow With Pytest",
            "--segment", ".",
            "--limit", "1",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        assert data["query"] == "TDD Workflow With Pytest"

    def test_explain_normalized_query_is_lowercase(self):
        """Verify normalized query is lowercase."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "TDD WORKFLOW",
            "--segment", ".",
            "--limit", "1",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        assert data["normalized_query"] == data["normalized_query"].lower()
        assert data["normalized_query"] == "tdd workflow"

    def test_explain_total_hits_matches_hits_length(self):
        """Verify total_hits matches length of hits array."""
        code, out, _ = run_cli([
            "ctx", "search",
            "--query", "test",
            "--segment", ".",
            "--limit", "3",
            "--explain"
        ])
        assert code == 0
        data = json.loads(out)

        assert data["total_hits"] == len(data["hits"])
