"""Pure domain evaluator for skill_hub corpus integrity.

This module is the single source of truth for the collapse-guard logic.
It has **no IO, no async, no framework dependencies** — it operates solely
on in-memory data derived from an already-admitted SkillManifest.

Publication-state semantics (canonical reference):
    - ``"blocked"``  → Corpus must NOT be promoted.  No live write, no
                       overwrite of ``.skill_hub_last_valid``.  The caller
                       MUST return an error; publication is forbidden.
    - ``"degraded"`` → Publication is allowed only when
                       ``SkillHubIntegrityConfig.allow_degraded`` is True.
                       Even so, ``.skill_hub_last_valid`` is NOT sealed —
                       a degraded set must never become the healthy fallback.
    - ``"healthy"``  → All required source families are present above their
                       minimum thresholds.  Publication proceeds normally and
                       ``.skill_hub_last_valid`` IS sealed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Iterable, Literal, Protocol

if TYPE_CHECKING:
    from src.domain.models import SkillHubIntegrityConfig

# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

PublicationState = Literal["healthy", "degraded", "blocked"]

REASON_ALL_SOURCES_PRESENT = "all_required_sources_present"
REASON_MISSING_SOURCES_DEGRADED = "missing_sources_allow_degraded"
REASON_MISSING_SOURCES_BLOCKED = "missing_sources_no_fallback_allowed"
REASON_NO_GUARD = "no_required_sources_configured"


class HasSource(Protocol):
    """Minimum surface required from a skill entry for integrity evaluation."""

    source: str


# ---------------------------------------------------------------------------
# Verdict dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SkillHubIntegrityVerdict:
    """Result of a corpus-integrity evaluation.

    This dataclass is the receipt carried into the promotion pipeline and
    persisted inside ``skill_hub_promotion_receipt.json``.

    Publication-state semantics (canonical reference):

    ``blocked``
        No promotion, no live write, no overwrite of ``.skill_hub_last_valid``.
        The caller MUST return an error; publication is forbidden.

    ``degraded``
        Publication is allowed only when
        ``SkillHubIntegrityConfig.allow_degraded`` is True.  Even so,
        ``.skill_hub_last_valid`` is NOT sealed — a degraded set must never
        become the healthy fallback.

    ``healthy``
        All required source families are present above their minimum
        thresholds.  Publication proceeds normally and
        ``.skill_hub_last_valid`` IS sealed.

    Fields
    ------
    publication_state:
        Canonical publication intent.  See above for semantics.
    observed_skill_count:
        Total number of skills evaluated (len of the manifest skills iterable).
    observed_source_count:
        Number of distinct source families observed in the corpus.
    observed_counts:
        Read-only mapping of source-family name → skill count
        (``MappingProxyType`` — mutation raises ``TypeError``).
    missing_sources:
        Source families from ``required_sources`` that did NOT meet the
        minimum threshold.  Empty tuple when healthy.
    required_sources:
        The full list of required sources taken from the policy config at
        evaluation time (snapshot copy — not a reference).
    min_skills_per_source:
        Threshold applied per required source during evaluation.
    reason_code:
        Machine-readable reason identifier for the verdict.  One of the
        ``REASON_*`` constants defined in this module.
    manifest_fingerprint:
        Hex digest identifying the manifest content evaluated.  Empty string
        when no fingerprint was supplied by the caller.
    corpus_hash:
        Deterministic hash of the observed corpus composition
        (source → count pairs, sorted).  Enables diff detection between
        two receipts without comparing full manifests.
    """

    publication_state: PublicationState
    observed_skill_count: int
    observed_source_count: int
    observed_counts: MappingProxyType[str, int]
    missing_sources: tuple[str, ...]
    required_sources: tuple[str, ...]
    min_skills_per_source: int
    reason_code: str
    manifest_fingerprint: str = ""
    corpus_hash: str = ""

    def as_receipt_block(self) -> dict[str, object]:
        """Serialise verdict to the canonical ``integrity`` block for receipts.

        This shape is the contract consumed by ``ContextService`` and the CLI
        warning layer.  Do not change field names without a schema version bump.
        """
        return {
            "verdict": self.publication_state,
            "observed_skill_count": self.observed_skill_count,
            "observed_source_count": self.observed_source_count,
            "observed_counts": dict(self.observed_counts),
            "missing_sources": list(self.missing_sources),
            "required_sources": list(self.required_sources),
            "min_skills_per_source": self.min_skills_per_source,
            "reason_code": self.reason_code,
            "manifest_fingerprint": self.manifest_fingerprint,
            "corpus_hash": self.corpus_hash,
        }


# ---------------------------------------------------------------------------
# Pure evaluator
# ---------------------------------------------------------------------------


def evaluate_corpus_integrity(
    manifest_skills: "Iterable[Any]",
    config: "SkillHubIntegrityConfig",
    manifest_fingerprint: str = "",
) -> SkillHubIntegrityVerdict:
    """Evaluate source-family coverage of a skill_hub promotion candidate.

    This is a **pure function**: it does not touch the filesystem, does not
    emit telemetry, and has no side-effects.  The caller is responsible for
    loading manifests and writing artifacts.

    Parameters
    ----------
    manifest_skills:
        All skill entries from the admitted SkillManifest.  Each entry must
        expose a ``source`` attribute (``str``).
    config:
        Integrity policy from ``TrifectaConfig.skill_hub_integrity``.
    manifest_fingerprint:
        Hex digest of the manifest content being evaluated.  Forwarded
        into the receipt for provenance traceability.  Optional.

    Returns
    -------
    SkillHubIntegrityVerdict
        Frozen verdict carrying all evidence needed for receipt emission,
        CLI warnings, and last_valid gating.
    """
    import hashlib as _hashlib

    raw_counts = dict(Counter(skill.source for skill in manifest_skills))
    observed_counts = MappingProxyType(raw_counts)
    observed_skill_count = sum(raw_counts.values())
    observed_source_count = len(raw_counts)

    # Deterministic corpus hash: sorted source→count pairs
    corpus_hash = _hashlib.sha256(
        ",".join(f"{k}:{v}" for k, v in sorted(raw_counts.items())).encode()
    ).hexdigest()[:16]

    def _verdict(**overrides: object) -> SkillHubIntegrityVerdict:
        base: dict[str, object] = {
            "observed_skill_count": observed_skill_count,
            "observed_source_count": observed_source_count,
            "observed_counts": observed_counts,
            "required_sources": config.required_sources,
            "min_skills_per_source": config.min_skills_per_source,
            "manifest_fingerprint": manifest_fingerprint,
            "corpus_hash": corpus_hash,
        }
        base.update(overrides)
        return SkillHubIntegrityVerdict(**base)  # type: ignore[arg-type]

    # Short-circuit: no guard configured → always healthy
    if not config.required_sources:
        return _verdict(
            publication_state="healthy",
            missing_sources=(),
            reason_code=REASON_NO_GUARD,
        )

    # Find source families that do NOT meet the minimum threshold
    missing: list[str] = [
        source
        for source in config.required_sources
        if observed_counts.get(source, 0) < config.min_skills_per_source
    ]
    missing_sources = tuple(sorted(missing))

    if not missing_sources:
        return _verdict(
            publication_state="healthy",
            missing_sources=(),
            reason_code=REASON_ALL_SOURCES_PRESENT,
        )

    # Some required sources are missing — decide between degraded and blocked
    publication_state: PublicationState = (
        "degraded" if config.allow_degraded else "blocked"
    )
    reason_code = (
        REASON_MISSING_SOURCES_DEGRADED
        if config.allow_degraded
        else REASON_MISSING_SOURCES_BLOCKED
    )

    return _verdict(
        publication_state=publication_state,
        missing_sources=missing_sources,
        reason_code=reason_code,
    )
