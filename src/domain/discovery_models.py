"""Domain models for discovery operations."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ImportInfo:
    """Represents an imported module or symbol."""

    name: str
    is_relative: bool
    level: int
    imported_names: tuple[str, ...]

    @property
    def is_from_import(self) -> bool:
        """Whether this is a 'from X import Y' statement."""
        return len(self.imported_names) > 0

    @property
    def is_wildcard(self) -> bool:
        """Whether this imports everything (from X import *)."""
        return "*" in self.imported_names


@dataclass(frozen=True)
class ExtractionResult:
    """Result of extracting imports from a source file."""

    imports: tuple[ImportInfo, ...]
    line_count: int
    warnings: tuple[str, ...]
