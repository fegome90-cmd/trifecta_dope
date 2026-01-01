"""
Symbol Selector DSL v0: Parse and resolve sym:// queries.

SYNTAX:
  sym://python/<qualified_name>
  sym://python/MyClass.method

RESOLUTION:
  1. Search skeleton maps by qualified_name
  2. Fail-closed: if ambiguous or 0 matches, return resolved=false
  3. If 1 match: return (file, range)
"""

import re
from dataclasses import dataclass
from typing import Optional

from src.application.ast_parser import SkeletonMapBuilder, SymbolInfo

__all__ = ["SymbolQuery", "SymbolResolver"]


@dataclass(frozen=True)
class SymbolQuery:
    """Parsed sym:// query."""

    language: str  # "python"
    qualified_name: str  # "MyClass.method"
    raw: str  # Original sym:// string

    @classmethod
    def parse(cls, query_str: str) -> Optional["SymbolQuery"]:
        """
        Parse sym:// DSL.

        Args:
            query_str: e.g. "sym://python/MyClass.method"

        Returns:
            SymbolQuery or None if parse fails
        """
        # Match: sym://language/qualified_name
        match = re.match(r"^sym://([a-z]+)/(.+)$", query_str)
        if not match:
            return None

        language, qualified = match.groups()
        if not language or not qualified:
            return None

        return cls(language=language, qualified_name=qualified, raw=query_str)


@dataclass(frozen=True)
class SymbolResolveResult:
    """Result of symbol resolution."""

    resolved: bool
    file: Optional[str] = None  # Relative path
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    matches: int = 0  # Total candidates found
    ambiguous: bool = False
    candidates: list[tuple[str, SymbolInfo]] = None  # type: ignore


class SymbolResolver:
    """
    Resolve sym:// queries against skeleton maps.

    Fail-closed: ambiguity → resolved=false (user must disambiguate)
    """

    def __init__(self, skeleton_builder: SkeletonMapBuilder) -> None:
        """Initialize resolver."""
        self.builder = skeleton_builder
        self._skeletons: dict[str, list[SymbolInfo]] = {}

    def add_skeleton(self, file_path: str, symbols: list[SymbolInfo]) -> None:
        """Register skeleton map for file."""
        self._skeletons[file_path] = symbols

    def resolve(
        self, query: SymbolQuery
    ) -> SymbolResolveResult:
        """
        Resolve symbol query against registered skeletons.

        Returns:
            SymbolResolveResult with resolved=True/False
        """
        if query.language != "python":
            # Only Python supported in v0
            return SymbolResolveResult(resolved=False)

        # Search across all skeleton maps
        candidates: list[tuple[str, SymbolInfo]] = []
        for file_path, symbols in self._skeletons.items():
            for symbol in symbols:
                if symbol.qualified_name == query.qualified_name:
                    candidates.append((file_path, symbol))

        # Fail-closed logic
        if len(candidates) == 0:
            return SymbolResolveResult(
                resolved=False,
                matches=0,
            )
        elif len(candidates) > 1:
            # Ambiguous: return top 5 candidates for user to choose
            return SymbolResolveResult(
                resolved=False,
                ambiguous=True,
                matches=len(candidates),
                candidates=candidates[:5],
            )
        else:
            # Exactly 1 match: resolved
            file_path, symbol = candidates[0]
            return SymbolResolveResult(
                resolved=True,
                file=file_path,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                matches=1,
                candidates=[(file_path, symbol)],
            )
