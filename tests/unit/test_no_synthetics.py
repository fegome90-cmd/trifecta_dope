"""Tests for eliminating vague_default_boost synthetic tokens.

These tests verify that the linter does NOT inject `agent.md`/`prime.md`
as default strong anchors for vague queries, preventing false-positive
ranking of irrelevant skills (code-review-agent, pae-agent, etc.).

RED phase: all 6 symptom tests should FAIL against the current linter
that still injects synthetics. GREEN after removing vague_default_boost.
"""

from src.domain.query_linter import classify_query, expand_query, lint_query
from src.application.context_service import ContextService
from src.domain.context_models import ContextChunk, ContextIndexEntry, ContextPack

from pathlib import Path


# --- Minimal config fixtures ---


def _no_anchors_cfg():
    """Empty anchors config — no strong/weak anchors defined."""
    return {"anchors": {"strong": {}, "weak": {}}}


def _no_aliases_cfg():
    """Empty aliases config."""
    return {}


def _anchors_with_agent_prime():
    """Config that defines agent.md and prime.md as strong anchors."""
    return {
        "anchors": {
            "strong": {
                "files": ["agent.md", "prime.md"],
            },
            "weak": {},
        }
    }


# --- Linter-level tests: verify synthetics are NOT injected ---


class TestLinterNoSynthetics:
    """Verify that expand_query does NOT inject agent.md/prime.md defaults."""

    def test_vague_single_token_no_synthetics(self):
        """A vague single-token query must NOT get agent.md/prime.md injected."""
        analysis = classify_query("backpressure", _no_anchors_cfg(), _no_aliases_cfg())
        result = expand_query("backpressure", analysis, _no_anchors_cfg())

        assert "agent.md" not in result["expanded_query"], (
            f"Linter injected agent.md into '{result['expanded_query']}'. "
            "vague_default_boost should not exist."
        )
        assert "prime.md" not in result["expanded_query"], (
            f"Linter injected prime.md into '{result['expanded_query']}'. "
            "vague_default_boost should not exist."
        )
        assert "vague_default_boost" not in result["reasons"], (
            "vague_default_boost reason should not appear."
        )

    def test_vague_two_token_no_synthetics(self):
        """A vague two-token query must NOT get agent.md/prime.md injected."""
        analysis = classify_query("test pattern", _no_anchors_cfg(), _no_aliases_cfg())
        result = expand_query("test pattern", analysis, _no_anchors_cfg())

        assert "agent.md" not in result["expanded_query"]
        assert "prime.md" not in result["expanded_query"]

    def test_go_query_no_synthetics(self):
        """'go' (2-char token, vague) must NOT get synthetics."""
        analysis = classify_query("go", _no_anchors_cfg(), _no_aliases_cfg())
        result = expand_query("go", analysis, _no_anchors_cfg())

        assert "agent.md" not in result["expanded_query"]
        assert "prime.md" not in result["expanded_query"]

    def test_lint_query_no_default_boost(self):
        """Full lint_query pipeline must not inject default synthetics."""
        plan = lint_query("xylophone", _no_anchors_cfg(), _no_aliases_cfg())

        assert "agent.md" not in plan["expanded_query"], (
            f"Full lint pipeline injected synthetics: '{plan['expanded_query']}'"
        )
        assert "prime.md" not in plan["expanded_query"]

    def test_lint_query_with_agent_prime_in_config_still_no_default(self):
        """Even when agent.md/prime.md are defined in anchors config,
        they must NOT be injected as defaults for unrelated vague queries."""
        analysis = classify_query("backpressure", _anchors_with_agent_prime(), _no_aliases_cfg())
        result = expand_query("backpressure", analysis, _anchors_with_agent_prime())

        # They might be detected as strong anchors IF they appear in the query
        # (which they don't for "backpressure"), but must NOT be injected as defaults.
        assert "vague_default_boost" not in result["reasons"], (
            "vague_default_boost should not fire even when agent.md is in config."
        )


# --- Search-level tests: verify no false-positive ranking ---


def _make_skill(name: str, title: str, body: str, token_est: int = 100) -> tuple:
    chunk = ContextChunk(
        id=f"skill:{name}",
        doc="skill",
        title_path=[title],
        text=body,
        char_count=len(body),
        token_est=token_est,
        source_path=title,
    )
    entry = ContextIndexEntry(
        id=f"skill:{name}",
        title_path_norm=title,
        preview=body[:60],
        token_est=token_est,
    )
    return chunk, entry


def _build_pack(skills):
    return ContextPack(
        segment="test",
        chunks=[s[0] for s in skills],
        index=[s[1] for s in skills],
    )


class TestSearchNoSyntheticFalsePositives:
    """Verify that synthetic-free queries don't rank irrelevant skills."""

    def test_backpressure_no_false_agent(self):
        """'backpressure' must NOT rank code-review-agent #1 via synthetics."""
        skills = [
            _make_skill(
                "code-review-agent", "code-review-agent.md", "Code review with agent.", 109
            ),
            _make_skill("pae-agent", "pae-agent.md", "PAE agent system.", 104),
            _make_skill("mcp-builder", "mcp-builder.md", "Build MCP servers.", 111),
        ]
        pack = _build_pack(skills)
        svc = ContextService(Path("."))
        svc._load_pack = lambda: (pack, "healthy")

        result = svc.search("backpressure", k=3)

        # No skill contains "backpressure" — result should be empty
        assert len(result.hits) == 0, (
            f"'backpressure' returned {len(result.hits)} hits when no skill contains it. "
            f"Top: {[h.id for h in result.hits]}"
        )

    def test_nonexistent_token_returns_empty(self):
        """A token that matches no skill must return 0 results."""
        skills = [
            _make_skill(
                "code-review-agent", "code-review-agent.md", "Code review with agent.", 109
            ),
            _make_skill("pae-agent", "pae-agent.md", "PAE agent system.", 104),
        ]
        pack = _build_pack(skills)
        svc = ContextService(Path("."))
        svc._load_pack = lambda: (pack, "healthy")

        result = svc.search("xylophone", k=3)

        assert len(result.hits) == 0, (
            f"'xylophone' returned {len(result.hits)} hits. Top: {[h.id for h in result.hits]}"
        )

    def test_go_no_false_agent(self):
        """'go' must NOT rank agents over go-related skills."""
        skills = [
            _make_skill("go-testing", "go-testing.md", "Go testing patterns for TUI.", 88),
            _make_skill("golang-patterns", "golang-patterns.md", "Go design patterns.", 84),
            _make_skill(
                "code-review-agent", "code-review-agent.md", "Code review with agent.", 109
            ),
            _make_skill("pae-agent", "pae-agent.md", "PAE agent system.", 104),
        ]
        pack = _build_pack(skills)
        svc = ContextService(Path("."))
        svc._load_pack = lambda: (pack, "healthy")

        # "go" passes through as 2-char fallback token
        # go-testing should rank above agents because "go" is in its title
        result = svc.search("go", k=4)

        if len(result.hits) > 0:
            ids = [h.id for h in result.hits]
            # go-testing should be #1 if present in results
            if "skill:go-testing" in ids:
                go_rank = ids.index("skill:go-testing")
                agent_ranks = [ids.index(a) for a in ids if "agent" in a]
                if agent_ranks:
                    assert go_rank < min(agent_ranks), (
                        f"go-testing (rank {go_rank}) should outrank agents "
                        f"(min rank {min(agent_ranks)}). Order: {ids}"
                    )


class TestStemAliasStillWorks:
    """Verify that stem expansion and alias pathways still work without synthetics."""

    def test_skills_still_matches_skill_hub_doctor(self):
        """'skills' must still match skill-hub-doctor via stem expansion alone."""
        skills = [
            _make_skill(
                "skill-hub-doctor", "skill-hub-doctor.md", "Diagnose skill-hub issues.", 100
            ),
            _make_skill("unrelated", "unrelated.md", "Something else.", 80),
        ]
        pack = _build_pack(skills)
        svc = ContextService(Path("."))
        svc._load_pack = lambda: (pack, "healthy")

        result = svc.search("skills", k=2)

        ids = [h.id for h in result.hits]
        assert "skill:skill-hub-doctor" in ids, (
            f"Stem expansion broken: 'skills' should match 'skill-hub-doctor'. Results: {ids}"
        )

    def test_guided_query_unchanged(self):
        """Guided queries (5+ tokens) must not be expanded with synthetics.

        With empty anchors config, a 5-token query is classified 'vague'
        (no strong anchors detected). But even if expanded, it must NOT
        contain agent.md/prime.md — vague_default_boost is removed.
        """
        plan = lint_query(
            "typescript test error class constructor",
            _no_anchors_cfg(),
            _no_aliases_cfg(),
        )

        # Regardless of classification, synthetics must not appear
        assert "agent.md" not in plan["expanded_query"], (
            f"Guided query got synthetics: '{plan['expanded_query']}'"
        )
        assert "prime.md" not in plan["expanded_query"]
