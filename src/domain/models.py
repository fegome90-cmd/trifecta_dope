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
        if not v or " " in v:
            raise ValueError("Segment must be non-empty and contain no spaces")
        return v.lower().replace("_", "-")


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
