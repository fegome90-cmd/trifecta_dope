"""Query classifier — detects relational and semantic predicates in natural language queries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class RelationalPredicate:
    """A detected relational intent from a query string."""

    relation: Literal["callers", "callees"]
    target: str


@dataclass(frozen=True)
class SemanticPredicate:
    """A detected semantic-resolution intent from a query string."""

    method: Literal["hover"]
    target: str


@dataclass(frozen=True)
class QueryClass:
    """Classification result for a query."""

    predicate: Optional[RelationalPredicate]
    semantic: Optional[SemanticPredicate]


# Patterns: (compiled_regex, relation, capture_group_index_for_target)
_CALLER_PATTERNS: list[tuple[re.Pattern[str], Literal["callers"]]] = [
    # EN
    (re.compile(r"who\s+calls\s+(\S+)", re.IGNORECASE), "callers"),
    (re.compile(r"callers\s+of\s+(\S+)", re.IGNORECASE), "callers"),
    # ES — "a", "al", "a la"
    (re.compile(r"qui[eé]n\s+llama\s+(?:a\s+la|al|a)\s+(\S+)", re.IGNORECASE), "callers"),
    (re.compile(r"quienes\s+llaman\s+(?:a\s+la|al|a)\s+(\S+)", re.IGNORECASE), "callers"),
]

_CALLEE_PATTERNS: list[tuple[re.Pattern[str], Literal["callees"]]] = [
    # EN
    (re.compile(r"what\s+does\s+(\S+)\s+call", re.IGNORECASE), "callees"),
    (re.compile(r"callees\s+of\s+(\S+)", re.IGNORECASE), "callees"),
    # ES
    (re.compile(r"qu[eé]\s+(?:llama|llaman)\s+(?:a\s+la|al|a)?\s*(\S+)", re.IGNORECASE), "callees"),
]

# Semantic patterns: (compiled_regex, method)
_SEMANTIC_HOVER_PATTERNS: list[tuple[re.Pattern[str], Literal["hover"]]] = [
    # EN — "what is X", "show me X"
    (re.compile(r"what\s+is\s+(\S+)", re.IGNORECASE), "hover"),
    (re.compile(r"show\s+me\s+(\S+)", re.IGNORECASE), "hover"),
    # ES — "qué es X", "mostrame X"
    (re.compile(r"qu[eé]\s+es\s+(\S+)", re.IGNORECASE), "hover"),
    (re.compile(r"mostrame\s+(\S+)", re.IGNORECASE), "hover"),
]


def classify_query(query: str) -> QueryClass:
    """Classify a query string to detect relational and semantic predicates.

    Pure function — no IO, no side effects.
    Returns QueryClass with predicate=None and/or semantic=None for
    non-matching queries.  A query can have neither, one, or both.
    """
    stripped = query.strip()
    if not stripped:
        return QueryClass(predicate=None, semantic=None)

    predicate: Optional[RelationalPredicate] = None

    # Try caller patterns first
    for pattern, relation in _CALLER_PATTERNS:
        match = pattern.search(stripped)
        if match:
            target = match.group(1).strip()
            if target:
                predicate = RelationalPredicate(relation=relation, target=target)
                break

    # Try callee patterns (only if no caller match)
    if predicate is None:
        for pattern, relation in _CALLEE_PATTERNS:
            match = pattern.search(stripped)
            if match:
                target = match.group(1).strip()
                if target:
                    predicate = RelationalPredicate(relation=relation, target=target)
                    break

    # Detect semantic predicate (independent of relational)
    semantic: Optional[SemanticPredicate] = None
    for pattern, method in _SEMANTIC_HOVER_PATTERNS:
        match = pattern.search(stripped)
        if match:
            target = match.group(1).strip()
            if target:
                semantic = SemanticPredicate(method=method, target=target)
                break

    return QueryClass(predicate=predicate, semantic=semantic)
