"""Query classifier — detects relational predicates in natural language queries."""

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
class QueryClass:
    """Classification result for a query."""

    predicate: Optional[RelationalPredicate]


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


def classify_query(query: str) -> QueryClass:
    """Classify a query string to detect relational predicates.

    Pure function — no IO, no side effects.
    Returns QueryClass with predicate=None for non-relational queries.
    """
    stripped = query.strip()
    if not stripped:
        return QueryClass(predicate=None)

    # Try caller patterns first
    for pattern, relation in _CALLER_PATTERNS:
        match = pattern.search(stripped)
        if match:
            target = match.group(1).strip()
            if not target:
                continue
            return QueryClass(
                predicate=RelationalPredicate(relation=relation, target=target)
            )

    # Try callee patterns
    for pattern, relation in _CALLEE_PATTERNS:
        match = pattern.search(stripped)
        if match:
            target = match.group(1).strip()
            if not target:
                continue
            return QueryClass(
                predicate=RelationalPredicate(relation=relation, target=target)
            )

    return QueryClass(predicate=None)
