"""Unit tests for skill_hub corpus integrity evaluator (pure domain).

Tests the evaluate_corpus_integrity() function and SkillHubIntegrityVerdict
in full isolation — no IO, no mocks, no fixtures beyond simple data classes.

Covers:
    - healthy verdict (all required sources present above threshold)
    - degraded verdict (missing sources + allow_degraded=True)
    - blocked verdict (missing sources + allow_degraded=False)
    - empty required_sources (guard disabled → always healthy)
    - min_skills_per_source threshold enforcement
    - observed_counts correctness
    - as_receipt_block() contract (all 8 required keys present)
    - reason_code values
    - verdicts are frozen (immutable)
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from src.domain.models import SkillHubIntegrityConfig
from src.domain.skill_hub_corpus_integrity import (
    REASON_ALL_SOURCES_PRESENT,
    REASON_MISSING_SOURCES_BLOCKED,
    REASON_MISSING_SOURCES_DEGRADED,
    REASON_NO_GUARD,
    evaluate_corpus_integrity,
)


# ---------------------------------------------------------------------------
# Minimal skill stub that satisfies the HasSource protocol
# ---------------------------------------------------------------------------


@dataclass
class _FakeSkill:
    source: str


def _skills(*sources: str) -> list[_FakeSkill]:
    """Build a list of fake skills with the given source names."""
    return [_FakeSkill(source=s) for s in sources]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _config(
    required: tuple[str, ...] = (),
    allow_degraded: bool = False,
    min_per_source: int = 1,
) -> SkillHubIntegrityConfig:
    return SkillHubIntegrityConfig(
        required_sources=required,
        allow_degraded=allow_degraded,
        min_skills_per_source=min_per_source,
    )


# ---------------------------------------------------------------------------
# Healthy verdicts
# ---------------------------------------------------------------------------


class TestHealthyVerdict:
    def test_all_required_sources_present(self) -> None:
        skills = _skills("pi-agent-skills", "claude-skills", "pi-agent-skills")
        config = _config(required=("pi-agent-skills", "claude-skills"))

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"
        assert verdict.missing_sources == ()
        assert verdict.reason_code == REASON_ALL_SOURCES_PRESENT

    def test_no_guard_configured_returns_healthy(self) -> None:
        """Empty required_sources disables the guard → always healthy."""
        skills = _skills("pi-agent-skills", "pi-agent-skills")
        config = _config(required=())

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"
        assert verdict.reason_code == REASON_NO_GUARD

    def test_no_guard_on_empty_corpus(self) -> None:
        """Empty corpus + no guard = healthy (guard is disabled, not a collapse)."""
        verdict = evaluate_corpus_integrity([], _config(required=()))

        assert verdict.publication_state == "healthy"
        assert verdict.observed_skill_count == 0

    def test_multiple_sources_all_above_threshold(self) -> None:
        skills = _skills(
            "a", "a", "b", "b", "c"
        )
        config = _config(required=("a", "b", "c"), min_per_source=1)

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"


# ---------------------------------------------------------------------------
# Degraded verdicts
# ---------------------------------------------------------------------------


class TestDegradedVerdict:
    def test_missing_source_with_allow_degraded_true(self) -> None:
        skills = _skills("pi-agent-skills", "pi-agent-skills", "pi-agent-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=True,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "degraded"
        assert "claude-skills" in verdict.missing_sources
        assert verdict.reason_code == REASON_MISSING_SOURCES_DEGRADED

    def test_all_sources_missing_with_allow_degraded(self) -> None:
        skills = _skills("other-source")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=True,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "degraded"
        assert set(verdict.missing_sources) == {"pi-agent-skills", "claude-skills"}


# ---------------------------------------------------------------------------
# Blocked verdicts
# ---------------------------------------------------------------------------


class TestBlockedVerdict:
    def test_missing_source_with_allow_degraded_false(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=False,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "blocked"
        assert "claude-skills" in verdict.missing_sources
        assert verdict.reason_code == REASON_MISSING_SOURCES_BLOCKED

    def test_completely_empty_corpus_blocked(self) -> None:
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=False,
        )

        verdict = evaluate_corpus_integrity([], config)

        assert verdict.publication_state == "blocked"
        assert set(verdict.missing_sources) == {"pi-agent-skills", "claude-skills"}


# ---------------------------------------------------------------------------
# min_skills_per_source threshold
# ---------------------------------------------------------------------------


class TestMinSkillsPerSourceThreshold:
    def test_source_below_min_threshold_is_missing(self) -> None:
        # claude-skills appears once but threshold requires 2
        skills = _skills("pi-agent-skills", "pi-agent-skills", "claude-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=False,
            min_per_source=2,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "blocked"
        assert "claude-skills" in verdict.missing_sources

    def test_source_exactly_at_min_threshold_is_present(self) -> None:
        skills = _skills("pi-agent-skills", "pi-agent-skills", "claude-skills", "claude-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=False,
            min_per_source=2,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"

    def test_default_min_threshold_is_one(self) -> None:
        skills = _skills("pi-agent-skills", "claude-skills")
        config = _config(required=("pi-agent-skills", "claude-skills"))

        verdict = evaluate_corpus_integrity(skills, config)

        assert config.min_skills_per_source == 1
        assert verdict.publication_state == "healthy"


# ---------------------------------------------------------------------------
# Observed counts correctness
# ---------------------------------------------------------------------------


class TestObservedCounts:
    def test_counts_match_actual_distribution(self) -> None:
        skills = _skills(
            "pi-agent-skills",
            "pi-agent-skills",
            "pi-agent-skills",
            "claude-skills",
            "codex-skills",
            "codex-skills",
        )
        config = _config(required=("pi-agent-skills", "claude-skills", "codex-skills"))

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.observed_counts["pi-agent-skills"] == 3
        assert verdict.observed_counts["claude-skills"] == 1
        assert verdict.observed_counts["codex-skills"] == 2
        assert verdict.observed_skill_count == 6
        assert verdict.observed_source_count == 3

    def test_counts_reflect_only_observed_sources(self) -> None:
        """Unrequired sources still appear in observed_counts — they are evidence."""
        skills = _skills("pi-agent-skills", "wildcard-source")
        config = _config(required=("pi-agent-skills",))

        verdict = evaluate_corpus_integrity(skills, config)

        assert "wildcard-source" in verdict.observed_counts
        assert verdict.publication_state == "healthy"

    def test_missing_sources_tuple_is_sorted(self) -> None:
        skills = _skills("x-source")
        config = _config(
            required=("z-source", "a-source", "m-source"),
            allow_degraded=True,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.missing_sources == tuple(sorted(verdict.missing_sources))


# ---------------------------------------------------------------------------
# as_receipt_block() contract
# ---------------------------------------------------------------------------

REQUIRED_RECEIPT_KEYS = {
    "verdict",
    "observed_skill_count",
    "observed_source_count",
    "observed_counts",
    "missing_sources",
    "required_sources",
    "min_skills_per_source",
    "reason_code",
    "manifest_fingerprint",
    "corpus_hash",
}


class TestReceiptBlock:
    def test_receipt_block_contains_all_required_keys(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config(required=("pi-agent-skills",))

        verdict = evaluate_corpus_integrity(skills, config)
        block = verdict.as_receipt_block()

        assert REQUIRED_RECEIPT_KEYS <= set(block.keys()), (
            f"Missing keys in receipt block: {REQUIRED_RECEIPT_KEYS - set(block.keys())}"
        )

    def test_receipt_block_verdict_matches_publication_state(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config(required=("pi-agent-skills", "claude-skills"), allow_degraded=True)

        verdict = evaluate_corpus_integrity(skills, config)
        block = verdict.as_receipt_block()

        assert block["verdict"] == verdict.publication_state

    def test_receipt_block_lists_are_serializable(self) -> None:
        """All list/dict values in the block must be JSON-serialisable types."""
        skills = _skills("pi-agent-skills", "claude-skills")
        config = _config(required=("pi-agent-skills", "claude-skills"))

        verdict = evaluate_corpus_integrity(skills, config)
        block = verdict.as_receipt_block()

        # Should not raise
        serialized = json.dumps(block)
        assert serialized  # non-empty

    @pytest.mark.parametrize(
        "state,expected_key",
        [
            ("healthy", REASON_ALL_SOURCES_PRESENT),
            ("degraded", REASON_MISSING_SOURCES_DEGRADED),
            ("blocked", REASON_MISSING_SOURCES_BLOCKED),
        ],
    )
    def test_receipt_block_reason_code_per_state(
        self, state: str, expected_key: str
    ) -> None:
        config_map: dict[str, SkillHubIntegrityConfig] = {
            "healthy": _config(required=("s",)),
            "degraded": _config(required=("s", "missing"), allow_degraded=True),
            "blocked": _config(required=("s", "missing"), allow_degraded=False),
        }
        skills_map: dict[str, list[_FakeSkill]] = {
            "healthy": _skills("s"),
            "degraded": _skills("s"),
            "blocked": _skills("s"),
        }

        verdict = evaluate_corpus_integrity(skills_map[state], config_map[state])
        block = verdict.as_receipt_block()

        assert block["reason_code"] == expected_key


# ---------------------------------------------------------------------------
# Immutability / frozen dataclass
# ---------------------------------------------------------------------------


class TestVerdictImmutability:
    def test_verdict_is_frozen(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)

        with pytest.raises((AttributeError, TypeError)):
            verdict.publication_state = "blocked"  # type: ignore[misc]

    def test_verdict_observed_counts_copy_is_independent(self) -> None:
        """Mutating the returned dict must not affect the verdict."""
        skills = _skills("pi-agent-skills")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)
        block = verdict.as_receipt_block()

        # mutate the returned dict
        block["observed_counts"]["injected"] = 999

        # original verdict is unaffected
        assert "injected" not in verdict.observed_counts


# ---------------------------------------------------------------------------
# Config policy snapshot
# ---------------------------------------------------------------------------


class TestConfigSnapshot:
    def test_required_sources_preserved_in_verdict(self) -> None:
        required = ("source-a", "source-b")
        skills = _skills("source-a", "source-b")
        config = _config(required=required)

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.required_sources == required

    def test_min_skills_per_source_preserved_in_verdict(self) -> None:
        config = _config(required=("s",), min_per_source=5)
        skills = _skills("s", "s", "s", "s", "s")

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.min_skills_per_source == 5


# ---------------------------------------------------------------------------
# Batch 1 additions: fingerprints, corpus_hash, publication semantics
# ---------------------------------------------------------------------------


class TestManifestFingerprint:
    """manifest_fingerprint is carried through from caller to receipt."""

    def test_fingerprint_forwarded_to_verdict(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config(required=("pi-agent-skills",))

        verdict = evaluate_corpus_integrity(
            skills, config, manifest_fingerprint="a1b2c3d4"
        )

        assert verdict.manifest_fingerprint == "a1b2c3d4"

    def test_fingerprint_defaults_to_empty_string(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.manifest_fingerprint == ""

    def test_fingerprint_appears_in_receipt_block(self) -> None:
        skills = _skills("s")
        config = _config(required=("s",))

        verdict = evaluate_corpus_integrity(
            skills, config, manifest_fingerprint="deadbeef"
        )
        block = verdict.as_receipt_block()

        assert block["manifest_fingerprint"] == "deadbeef"

    def test_fingerprint_is_json_serializable(self) -> None:
        skills = _skills("s")
        config = _config()

        verdict = evaluate_corpus_integrity(
            skills, config, manifest_fingerprint="abc123"
        )
        serialized = json.dumps(verdict.as_receipt_block())

        assert "abc123" in serialized


class TestCorpusHash:
    """corpus_hash is a deterministic hash of source→count composition."""

    def test_corpus_hash_is_16_hex_chars(self) -> None:
        skills = _skills("a", "b")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)

        assert len(verdict.corpus_hash) == 16
        assert all(c in "0123456789abcdef" for c in verdict.corpus_hash)

    def test_same_composition_same_hash(self) -> None:
        skills_a = _skills("x", "x", "y")
        skills_b = _skills("x", "y", "x")  # same counts, different order
        config = _config()

        v1 = evaluate_corpus_integrity(skills_a, config)
        v2 = evaluate_corpus_integrity(skills_b, config)

        assert v1.corpus_hash == v2.corpus_hash

    def test_different_composition_different_hash(self) -> None:
        skills_a = _skills("a", "a", "b")
        skills_b = _skills("a", "b", "b")
        config = _config()

        v1 = evaluate_corpus_integrity(skills_a, config)
        v2 = evaluate_corpus_integrity(skills_b, config)

        assert v1.corpus_hash != v2.corpus_hash

    def test_corpus_hash_appears_in_receipt_block(self) -> None:
        skills = _skills("s")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)
        block = verdict.as_receipt_block()

        assert "corpus_hash" in block
        assert isinstance(block["corpus_hash"], str)
        assert len(block["corpus_hash"]) == 16

    def test_empty_corpus_has_deterministic_hash(self) -> None:
        config = _config()

        v1 = evaluate_corpus_integrity([], config)
        v2 = evaluate_corpus_integrity([], config)

        assert v1.corpus_hash == v2.corpus_hash


class TestPublicationSemantics:
    """Enforce the three-state publication contract."""

    def test_blocked_no_promotion(self) -> None:
        """blocked means: no promotion, no live write, no last_valid overwrite."""
        skills = _skills("pi-agent-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=False,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "blocked"
        assert verdict.missing_sources != ()
        assert verdict.reason_code == REASON_MISSING_SOURCES_BLOCKED

    def test_degraded_publish_allowed_but_no_seal(self) -> None:
        """degraded means: publish allowed but never seal last_valid."""
        skills = _skills("pi-agent-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
            allow_degraded=True,
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "degraded"
        assert verdict.missing_sources != ()
        assert verdict.reason_code == REASON_MISSING_SOURCES_DEGRADED

    def test_healthy_publish_and_seal(self) -> None:
        """healthy means: full publication + seal last_valid."""
        skills = _skills("pi-agent-skills", "claude-skills")
        config = _config(
            required=("pi-agent-skills", "claude-skills"),
        )

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"
        assert verdict.missing_sources == ()
        assert verdict.reason_code == REASON_ALL_SOURCES_PRESENT

    def test_no_guard_is_healthy_with_seal(self) -> None:
        """No guard configured => healthy (publish + seal)."""
        skills = _skills("anything")
        config = _config(required=())

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"
        assert verdict.reason_code == REASON_NO_GUARD


# ---------------------------------------------------------------------------
# Review fix additions: tuple input + MappingProxyType immutability
# ---------------------------------------------------------------------------


class TestTupleInputPath:
    """Exercise the tuple branch of the union type."""

    def test_tuple_input_accepted(self) -> None:
        skills = tuple(_skills("pi-agent-skills", "claude-skills"))
        config = _config(required=("pi-agent-skills", "claude-skills"))

        verdict = evaluate_corpus_integrity(skills, config)

        assert verdict.publication_state == "healthy"
        assert verdict.observed_skill_count == 2


class TestMappingProxyImmutability:
    """MappingProxyType prevents direct mutation of observed_counts."""

    def test_observed_counts_rejects_mutation(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)

        with pytest.raises(TypeError):
            verdict.observed_counts["injected"] = 999

    def test_observed_counts_rejects_deletion(self) -> None:
        skills = _skills("pi-agent-skills")
        config = _config()

        verdict = evaluate_corpus_integrity(skills, config)

        with pytest.raises(TypeError):
            del verdict.observed_counts["pi-agent-skills"]
