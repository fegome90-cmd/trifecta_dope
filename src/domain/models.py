"""Domain Models for Trifecta."""

from dataclasses import dataclass
from pydantic import BaseModel, field_validator


class TrifectaConfig(BaseModel):
    """Configuration for a Trifecta pack."""

    segment: str
    scope: str
    repo_root: str
    default_profile: str = "impl_patch"
    last_verified: str = ""

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
        from src.domain.naming import normalize_segment_id

        return normalize_segment_id(self.segment)


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
