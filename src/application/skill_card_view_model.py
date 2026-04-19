from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SkillCardViewModel:
    """Canonical view model representing a skill card.

    Acts as the single source of truth format for skill card rendering,
    serving as the boundary between core search pipeline and CLI display.
    """

    id: str
    name: str
    path: str
    source: str
    description: str
    authority_state: Literal["healthy", "degraded"]
    
    search_hints: str | None = None
    triggers: tuple[str, ...] = ()
    relevance: float = 0.0

    def __post_init__(self) -> None:
        if self.id is None or self.name is None:
            raise ValueError("id and name must be provided, not None")
        if self.authority_state not in ("healthy", "degraded"):
            raise ValueError(f"authority_state must be 'healthy' or 'degraded', got {self.authority_state!r}")
