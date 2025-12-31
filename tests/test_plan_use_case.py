"""Regression tests for ctx.plan router discipline."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.application.plan_use_case import PlanUseCase


@pytest.fixture
def mock_telemetry():
    """Mock telemetry instance."""
    telemetry = MagicMock()
    telemetry.incr = MagicMock()
    telemetry.event = MagicMock()
    return telemetry


@pytest.fixture
def mock_filesystem():
    """Mock filesystem instance."""
    return MagicMock()


@pytest.fixture
def temp_ctx_dir(tmp_path):
    """Create a temporary ctx directory with test files."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    # Create aliases.yaml with schema v2
    aliases = {
        "schema_version": 2,
        "features": {
            "test_feature": {
                "priority": 3,
                "triggers": [
                    {
                        "phrase": "test trigger phrase",
                        "terms": ["test", "trigger", "phrase"],
                        "high_signal": False,
                        "notes": "Test trigger",
                    }
                ],
                "bundle": {"chunks": ["chunk1", "chunk2"], "paths": ["path1.py", "path2.py"]},
            },
            "generic_feature": {
                "priority": 1,
                "triggers": [
                    {
                        "phrase": "generic system overview",
                        "terms": ["generic", "system", "overview"],
                        "high_signal": False,
                        "notes": "Generic trigger - should NOT match specific queries",
                    }
                ],
                "bundle": {"chunks": ["gen_chunk1"], "paths": ["gen_path1.py"]},
            },
        },
    }

    aliases_path = ctx_dir / "aliases.yaml"
    aliases_path.write_text(json.dumps(aliases))

    # Create bundle path files so assertion checks pass
    (tmp_path / "path1.py").write_text("# path1")
    (tmp_path / "path2.py").write_text("# path2")
    (tmp_path / "gen_path1.py").write_text("# gen_path1")

    # Create a minimal PRIME file
    prime_content = """
# Test Prime

## [INDEX] Index para ctx.plan

### index.entrypoints

| Path | Razón |
|------|-------|
| `README.md` | Entry point |
| `skill.md` | Rules |

### index.feature_map
(Moved to aliases.yaml)
"""
    prime_path = ctx_dir / "prime_test.md"
    prime_path.write_text(prime_content)

    return tmp_path, ctx_dir


def test_plan_prefers_feature_over_alias_over_fallback(
    mock_filesystem, mock_telemetry, temp_ctx_dir
):
    """Test L1 (feature:) takes precedence over L2 (alias) over L3 (fallback)."""
    tmp_path, ctx_dir = temp_ctx_dir
    use_case = PlanUseCase(mock_filesystem, mock_telemetry)

    # L1: Explicit feature should match
    result = use_case.execute(tmp_path, "feature:test_feature some extra text")
    assert result["plan_hit"] is True
    assert result["selected_feature"] == "test_feature"
    assert result["selected_by"] == "feature"
    assert "L1: Explicit feature:test_feature" in result["budget_est"]["why"]

    # L2: Alias should match when no L1
    result = use_case.execute(tmp_path, "this matches test trigger phrase")
    assert result["plan_hit"] is True
    assert result["selected_feature"] == "test_feature"
    assert result["selected_by"] == "alias"
    assert result["match_terms_count"] >= 2

    # L3: Fallback when no match
    result = use_case.execute(tmp_path, "completely unrelated query with no matches")
    assert result["plan_hit"] is False
    assert result["selected_by"] == "fallback"
    assert "entrypoints" in result["budget_est"]["why"]


def test_plan_does_not_match_generic_triggers(mock_filesystem, mock_telemetry, temp_ctx_dir):
    """Test that generic triggers don't capture specific queries (anti-thesaurus)."""
    tmp_path, ctx_dir = temp_ctx_dir
    use_case = PlanUseCase(mock_filesystem, mock_telemetry)

    # Generic feature has "generic system overview" trigger
    # It should NOT match specific queries like "generic feature for telemetry"
    result = use_case.execute(tmp_path, "generic feature for telemetry")

    # With only 2 matching terms ("generic", "feature"), it might match if priority is high
    # The key is that it shouldn't match EVERYTHING with "generic" in it
    # A truly specific query should either:
    # 1. Match a more specific feature, or
    # 2. Fall back to entrypoints

    # For this test, we verify the matching is selective
    # If it matched, it should have good reason (>=2 terms)
    if result["plan_hit"]:
        assert result["match_terms_count"] >= 2, "Generic matches should require >=2 terms"
        assert result["matched_trigger"] == "generic system overview"
    else:
        # It's also acceptable to fall back for ambiguous queries
        assert result["selected_by"] == "fallback"


def test_plan_returns_why_selected_by(mock_filesystem, mock_telemetry, temp_ctx_dir):
    """Test that result includes selected_by, match_terms_count, and reason."""
    tmp_path, ctx_dir = temp_ctx_dir
    use_case = PlanUseCase(mock_filesystem, mock_telemetry)

    # Test L1 (feature)
    result = use_case.execute(tmp_path, "feature:test_feature query")
    assert result["selected_by"] == "feature"
    assert "why" in result["budget_est"]
    assert len(result["budget_est"]["why"]) > 0

    # Test L2 (alias)
    result = use_case.execute(tmp_path, "test trigger phrase here")
    assert result["selected_by"] == "alias"
    assert result["match_terms_count"] >= 2
    assert result["matched_trigger"] is not None
    assert "L3: Alias match" in result["budget_est"]["why"]

    # Test L3 (fallback)
    result = use_case.execute(tmp_path, "no match here")
    assert result["selected_by"] == "fallback"
    assert "L4: No feature match" in result["budget_est"]["why"]


def test_repo_map_generation_is_capped_and_deterministic():
    """Test that generated stubs have size limits and produce same output for same input."""
    # This test verifies the stubs in _ctx/generated/ are capped

    generated_dir = Path("_ctx/generated")
    if not generated_dir.exists():
        pytest.skip("_ctx/generated/ does not exist yet")

    repo_map_path = generated_dir / "repo_map.md"
    symbols_stub_path = generated_dir / "symbols_stub.md"

    if repo_map_path.exists():
        content = repo_map_path.read_text()
        lines = content.splitlines()

        # Cap: Should not exceed ~300 lines
        assert len(lines) <= 300, f"repo_map.md too large: {len(lines)} lines"

        # Deterministic: Should have stable headers
        assert "# Trifecta Dope - Repository Map" in content

    if symbols_stub_path.exists():
        content = symbols_stub_path.read_text()

        # Cap: Should not exceed ~300 lines
        lines = content.splitlines()
        assert len(lines) <= 300, f"symbols_stub.md too large: {len(lines)} lines"

        # Deterministic: Should have stable headers
        assert "# Symbol Navigation" in content


def test_plan_fail_closed_on_invalid_feature(mock_filesystem, mock_telemetry, temp_ctx_dir):
    """Test that feature:unknown_id fails closed (doesn't match)."""
    tmp_path, ctx_dir = temp_ctx_dir
    use_case = PlanUseCase(mock_filesystem, mock_telemetry)

    # Try to use a non-existent feature
    result = use_case.execute(tmp_path, "feature:nonexistent some query")

    # Should NOT match - fail closed
    assert result["plan_hit"] is False
    assert result["selected_by"] == "fallback"


def test_plan_high_signal_trigger_matches_single_term(mock_filesystem, mock_telemetry, tmp_path):
    """Test that high_signal triggers can match with 1 term."""
    # Create ctx with high_signal trigger
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()

    aliases = {
        "schema_version": 2,
        "features": {
            "high_sig_feature": {
                "priority": 5,
                "triggers": [
                    {
                        "phrase": "OpenTelemetry",
                        "terms": ["OpenTelemetry"],
                        "high_signal": True,
                        "notes": "Specific term that should auto-match",
                    }
                ],
                "bundle": {"chunks": ["otel_chunk"], "paths": ["otel.py"]},
            }
        },
    }

    aliases_path = ctx_dir / "aliases.yaml"
    aliases_path.write_text(json.dumps(aliases))

    # Create bundle path file so assertion checks pass
    (tmp_path / "otel.py").write_text("# otel")

    # Create minimal PRIME
    prime_path = ctx_dir / "prime_test.md"
    prime_path.write_text(
        "# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |"
    )

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)

    # Should match with just 1 term because it's high_signal
    result = use_case.execute(tmp_path, "tell me about OpenTelemetry")

    assert result["plan_hit"] is True
    assert result["selected_feature"] == "high_sig_feature"
    assert result["selected_by"] == "alias"


def test_l2_specificity_beats_priority_for_multiword_trigger(
    mock_filesystem, mock_telemetry, tmp_path
):
    """Multiword trigger should beat single-word trigger even if priority is lower."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "telemetry_feature": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            },
            "symbol_surface": {
                "priority": 2,
                "nl_triggers": ["telemetry class"],
                "bundle": {"chunks": ["c2"], "paths": ["p2.py"]},
            },
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (tmp_path / "p2.py").write_text("# p2")
    (ctx_dir / "prime_test.md").write_text(
        "# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |"
    )

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "how is the telemetry class constructed")
    assert result["selected_feature"] == "symbol_surface"
    assert result["selected_by"] == "nl_trigger"


def test_l2_single_word_clamp_blocks_without_support_terms(
    mock_filesystem, mock_telemetry, tmp_path
):
    """Single-word trigger without support terms should be clamped to fallback."""
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "telemetry_feature": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            }
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (ctx_dir / "prime_test.md").write_text(
        "# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razón |\n|------|-------|\n| `README.md` | Entry |"
    )

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "telemetry")
    assert result["selected_by"] == "fallback"
    assert result["l2_warning"] == "weak_single_word_trigger"
