"""Unit tests for IDF-weighted scoring in ContextService.

These tests validate that token rarity (IDF) is factored into ranking,
so rare/specific tokens contribute more than common/generic ones.

RED phase: these should FAIL against the current flat-weighting scoring.
"""

from pathlib import Path


from src.application.context_service import ContextService
from src.domain.context_models import ContextChunk, ContextIndexEntry, ContextPack


def _make_skill(name: str, title: str, body: str, token_est: int = 80) -> tuple[ContextChunk, ContextIndexEntry]:
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
            _make_skill("typescript-pro", "typescript-pro.md",
                        "TypeScript types generics utility types strict mode.", token_est=120),
            _make_skill("go-testing", "go-testing.md",
                        "Go testing patterns.", token_est=80),
            _make_skill("cpp-testing", "cpp-testing.md",
                        "C++ testing patterns.", token_est=80),
            _make_skill("python-testing", "python-testing.md",
                        "Python testing patterns.", token_est=80),
            _make_skill("test-driven-development", "test-driven-development.md",
                        "TDD workflow.", token_est=82),
            _make_skill("e2e-testing", "e2e-testing.md",
                        "End-to-end testing guide.", token_est=85),
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
            _make_skill("another-test", "another-test-skill.md", "More test content.", token_est=50),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        result = service.search("rare test", k=3)

        # At least one hit should have idf_weight in score_details
        has_idf = any(
            "idf_weights" in h.score_details
            for h in result.hits
            if h.score_details
        )
        assert has_idf, "score_details should contain idf_weights for explainability"

    def test_two_common_tokens_do_not_beat_one_rare_token(self):
        """Even with 2 common-token matches, 1 rare-token match should still win."""
        skills = [
            _make_skill("rare-match", "unique-framework.md",
                        "A very specific framework.", token_est=60),
            _make_skill("common-a", "test-helpers.md",
                        "Test helpers for testing.", token_est=60),
            _make_skill("common-b", "test-utils.md",
                        "Test utilities for testing.", token_est=60),
            _make_skill("common-c", "testing-guide.md",
                        "Guide for testing.", token_est=60),
            _make_skill("common-d", "testing-tools.md",
                        "Tools for testing.", token_est=60),
        ]
        pack = _build_pack(skills)

        service = ContextService(Path("."))
        service._load_pack = lambda: (pack, "healthy")

        # "unique test" — 'unique' is rare (1 skill), 'test' is common (4 skills)
        result = service.search("unique test", k=5)

        ids = [h.id for h in result.hits]
        # rare-match matches 'unique' in title — should rank #1
        assert ids[0] == "skill:rare-match", (
            f"rare-match should be #1, got {ids[0]}. Order: {ids}"
        )

    def test_stem_expansion_still_works_with_idf(self):
        """Stem expansion (skills->skill) must still function after IDF is added."""
        skills = [
            _make_skill("skill-hub-doctor", "skill-hub-doctor.md",
                        "Diagnose skill-hub issues.", token_est=100),
            _make_skill("unrelated", "unrelated.md",
                        "Something else entirely.", token_est=80),
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
