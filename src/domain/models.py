"""Domain Models for Trifecta."""

from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator


class SkillHubIntegrityConfig(BaseModel):
    """Corpus-integrity policy for skill_hub promotion.

    Governs which source families must be present in a promoted candidate and
    whether a corpus that fails that requirement can still be published in an
    explicit degraded state (vs. being fully blocked).

    Fields
    ------
    required_sources:
        Source-family names that MUST appear in the promoted candidate.
        An empty tuple disables the guard (default: no requirements).
    min_skills_per_source:
        Minimum number of skills that must come from each required source for
        that source to be considered "present".  Defaults to 1 (any presence).
    allow_degraded:
        If True, a corpus that is missing required sources is published with
        ``publication_state = "degraded"`` instead of being blocked.
        Defaults to False (fail-closed).
    """

    required_sources: tuple[str, ...] = ()
    min_skills_per_source: int = Field(default=1, ge=1)
    allow_degraded: bool = False


class TrifectaConfig(BaseModel):
    """Configuration for a Trifecta pack."""

    segment: str
    scope: str
    repo_root: str
    default_profile: str = "impl_patch"
    last_verified: str = ""
    skill_hub_integrity: SkillHubIntegrityConfig = Field(
        default_factory=SkillHubIntegrityConfig
    )

    @field_validator("segment")
    @classmethod
    def validate_segment(cls, v: str) -> str:
        """Validate segment is non-empty (preserve original value)."""
        if not v or not v.strip():
            raise ValueError("Segment must be non-empty")
        return v  # Preserve original

    @property
    def segment_id(self) -> str:
        """Derive normalized segment ID from segment name."""
        from src.domain.segment_resolver import get_segment_slug

        return get_segment_slug(self.segment)


class TrifectaPack(BaseModel):
    """Represents a complete Trifecta pack."""

    config: TrifectaConfig
    skill_content: str
    prime_content: str
    agent_content: str
    session_content: str
    readme_content: str = ""

    @property
    def skill_line_count(self) -> int:
        return len(self.skill_content.strip().split("\n"))


class ValidationResult(BaseModel):
    """Result of validating a Trifecta pack."""

    passed: bool
    errors: list[str] = []
    warnings: list[str] = []


# =============================================================================
# Context Pack Models (MVP - Progressive Disclosure)
# =============================================================================


@dataclass(frozen=True)
class SourceFile:
    """Metadata for a source file in the context pack."""

    path: str
    sha256: str
    chars: int


@dataclass(frozen=True)
class DigestEntry:
    """Entry in the digest (top-N most relevant chunks)."""

    doc: str
    chunk_id: str
    summary: str


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadata for a chunk (index entry)."""

    id: str
    doc: str
    title: str
    token_est: int


@dataclass(frozen=True)
class Chunk:
    """Full chunk with content."""

    id: str
    doc: str
    title: str
    text: str
    token_est: int


@dataclass(frozen=True)
class ContextPack:
    """Complete context pack (schema v1)."""

    schema_version: int
    segment_id: str
    created_at: str
    source_files: list[SourceFile]
    digest: list[DigestEntry]
    index: list[ChunkMetadata]
    chunks: list[Chunk]
