"""Domain Models for Trifecta."""

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
    warnings: list[str] = []
