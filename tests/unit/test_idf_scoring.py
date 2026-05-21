"""Unit tests for IDF-weighted scoring in ContextService.

These tests validate that token rarity (IDF) is factored into ranking,
so rare/specific tokens contribute more than common/generic ones.

RED phase: these should FAIL against the current flat-weighting scoring.
"""

from pathlib import Path


from src.application.context_service import ContextService
from src.domain.context_models import ContextChunk, ContextIndexEntry, ContextPack


def _make_skill(
    name: str, title: str, body: str, token_est: int = 80
) -> tuple[ContextChunk, ContextIndexEntry]:
    """Helper to build a chunk+index pair for a skill."""
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


def _build_pack(skills: list[tuple[ContextChunk, ContextIndexEntry]]) -> ContextPack:
    """Build a ContextPack from a list of (chunk, entry) tuples."""
    chunks = [s[0] for s in skills]
    index = [s[1] for s in skills]
    return ContextPack(segment="test", chunks=chunks, index=index)


class TestIDFRanking:
    """IDF weighting: rare tokens must outweigh common tokens."""

    def test_rare_token_beats_common_token_in_identity(self):
        """A skill matching a RARE token must outrank one matching a COMMON token.

        Setup:
        - 'typescript-pro' matches 'typescript' (rare: only 1 skill has it in title)
        - 'go-testing' matches 'test' (common: many skills have 'test' in title)
        - Query: "typescript test"

        Expected: typescript-pro should rank #1 because 'typescript' is more
        discriminative than 'test'.
        """
        # Build a corpus where 'test' appears in many titles but 'typescript' in only 1
        skills = [
            _make_skill(
                "typescript-pro",
                "typescript-pro.md",
                "TypeScript types generics utility types strict mode.",
                token_est=120,
            ),
            _make_skill("go-testing", "go-testing.md", "Go testing patterns.", token_est=80),
            _make_skill("cpp-testing", "cpp-testing.md", "C++ testing patterns.", token_est=80),
            _make_skill(
                "python-testing", "python-testing.md", "Python testing patterns.", token_est=80
            ),
            _make_skill(
                "test-driven-development",
                "test-driven-development.md",
                "TDD workflow.",
                token_est=82,
            ),
            _make_skill("e2e-testing", "e2e-testing.md", "End-to-end testing guide.", token_est=85),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        result = service.search("typescript test", k=6)

        # The typescript-pro skill must be in top results
        ids = [h.id for h in result.hits]
        assert "skill:typescript-pro" in ids, f"typescript-pro not in results: {ids}"

        # typescript-pro must rank above go-testing
        # (both match one token in title, but 'typescript' is rarer)
        ts_rank = ids.index("skill:typescript-pro")
        go_rank = ids.index("skill:go-testing") if "skill:go-testing" in ids else 999
        assert ts_rank < go_rank, (
            f"typescript-pro (rank {ts_rank}) should outrank go-testing (rank {go_rank}). "
            f"Order: {ids}"
        )

    def test_idf_values_appear_in_score_details(self):
        """score_details should contain idf_weight fields for transparency."""
        skills = [
            _make_skill("rare-skill", "rare-skill.md", "Unique content.", token_est=50),
            _make_skill("common-skill", "common-test-skill.md", "Test content.", token_est=50),
            _make_skill(
                "another-test", "another-test-skill.md", "More test content.", token_est=50
            ),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        result = service.search("rare test", k=3)

        # At least one hit should have idf_weight in score_details
        has_idf = any("idf_weights" in h.score_details for h in result.hits if h.score_details)
        assert has_idf, "score_details should contain idf_weights for explainability"

    def test_two_common_tokens_do_not_beat_one_rare_token(self):
        """Even with 2 common-token matches, 1 rare-token match should still win."""
        skills = [
            _make_skill(
                "rare-match", "unique-framework.md", "A very specific framework.", token_est=60
            ),
            _make_skill("common-a", "test-helpers.md", "Test helpers for testing.", token_est=60),
            _make_skill("common-b", "test-utils.md", "Test utilities for testing.", token_est=60),
            _make_skill("common-c", "testing-guide.md", "Guide for testing.", token_est=60),
            _make_skill("common-d", "testing-tools.md", "Tools for testing.", token_est=60),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        # "unique test" — 'unique' is rare (1 skill), 'test' is common (4 skills)
        result = service.search("unique test", k=5)

        ids = [h.id for h in result.hits]
        # rare-match matches 'unique' in title — should rank #1
        assert ids[0] == "skill:rare-match", f"rare-match should be #1, got {ids[0]}. Order: {ids}"

    def test_stem_expansion_still_works_with_idf(self):
        """Stem expansion (skills->skill) must still function after IDF is added."""
        skills = [
            _make_skill(
                "skill-hub-doctor",
                "skill-hub-doctor.md",
                "Diagnose skill-hub issues.",
                token_est=100,
            ),
            _make_skill("unrelated", "unrelated.md", "Something else entirely.", token_est=80),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        # "skills" should still match "skill-hub-doctor" via stem expansion
        result = service.search("skills", k=2)

        ids = [h.id for h in result.hits]
        assert "skill:skill-hub-doctor" in ids, (
            f"Stem expansion broken: 'skills' should match 'skill-hub-doctor'. Results: {ids}"
        )

    def test_synthetic_linter_tokens_get_neutral_idf(self):
        """Tokens with dots (linter synthetics like 'agent.md') must not inflate IDF.

        The query linter adds synthetic tokens ('agent.md', 'prime.md') to vague
        queries. These have high IDF but are NOT user intent — they must get
        neutral IDF=1.0 so they don't artificially boost skills matching the
        synthetic token's stem (e.g. 'agent' matching 'code-review-agent').
        """
        # Simulate linter-expanded query: "typescript agent.md prime.md"
        skills = [
            _make_skill(
                "typescript-pro",
                "typescript-pro.md",
                "TypeScript types generics.",
                token_est=120,
            ),
            _make_skill(
                "code-review-agent",
                "code-review-agent.md",
                "Code review with agent.",
                token_est=109,
            ),
            _make_skill(
                "pae-agent",
                "pae-agent.md",
                "PAE agent system.",
                token_est=104,
            ),
            _make_skill(
                "mcp-builder",
                "mcp-builder.md",
                "Build MCP servers.",
                token_est=111,
            ),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        # Query as the linter would expand it
        result = service.search("typescript agent.md prime.md", k=4)

        ids = [h.id for h in result.hits]
        # typescript-pro must rank #1 — the 'typescript' token is the real user intent
        # 'agent.md' and 'prime.md' are synthetics that should NOT boost agent skills
        assert ids[0] == "skill:typescript-pro", (
            f"typescript-pro should be #1 even with synthetic linter tokens. "
            f"Got {ids[0]}. Order: {ids}"
        )

        # Verify synthetic tokens got neutral IDF
        ts_hit = [h for h in result.hits if h.id == "skill:typescript-pro"][0]
        idf = ts_hit.score_details.get("idf_weights", {})
        assert idf.get("agent.md") == 1.0, (
            f"Synthetic token 'agent.md' should have IDF=1.0, got {idf.get('agent.md')}"
        )
        assert idf.get("prime.md") == 1.0, (
            f"Synthetic token 'prime.md' should have IDF=1.0, got {idf.get('prime.md')}"
        )
