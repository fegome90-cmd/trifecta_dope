"""Tests for dual-family alias canonical matching (AUTH-001, AUTH-002, AUTH-003).

The alias matching logic lives as inline Python in scripts/skill-hub.
We extract and test it independently here.
"""

import json
import re


def _run_alias_match(explain_json_str: str) -> str:
    """Replicate the alias matching logic from scripts/skill-hub inline Python.

    Returns the canonical alias match term, or "" if no match.
    """
    try:
        data = json.loads(explain_json_str)
    except json.JSONDecodeError:
        return ""

    expanded_terms = data.get("expansions", {}).get("expanded_terms", [])
    hits = data.get("hits", [])
    if not hits:
        return ""

    top_ref = hits[0].get("ref", "")
    for term in expanded_terms:
        if not re.fullmatch(r"[a-z0-9-]+", term):
            continue
        repo_prefix = f"repo:{term}.md:"
        skill_prefix = f"skill:{term}:"
        for hit in hits:
            ref = hit.get("ref", "")
            if ref.startswith(repo_prefix) or ref.startswith(skill_prefix):
                if ref != top_ref:
                    return term
                else:
                    return ""
    return ""


def _make_explain_json(hits: list[dict], expanded_terms: list[str] | None = None) -> str:
    """Build a minimal explain JSON for testing."""
    return json.dumps({
        "expansions": {"expanded_terms": expanded_terms or []},
        "hits": hits,
    })


def test_alias_match_skill_ref():
    """AUTH-001: skill:{term}: ref MUST be recognized as canonical."""
    data = _make_explain_json(
        hits=[
            {"ref": "repo:other.md:something", "score": 0.9},
            {"ref": "skill:python-patterns:some-chunk", "score": 0.8},
        ],
        expanded_terms=["python-patterns"],
    )

    result = _run_alias_match(data)
    assert result == "python-patterns"


def test_alias_match_legacy_ref():
    """AUTH-002: repo:{term}.md: ref MUST still be recognized."""
    data = _make_explain_json(
        hits=[
            {"ref": "repo:other.md:something", "score": 0.9},
            {"ref": "repo:python-patterns.md:some-chunk", "score": 0.8},
        ],
        expanded_terms=["python-patterns"],
    )

    result = _run_alias_match(data)
    assert result == "python-patterns"


def test_alias_match_rejects_substring():
    """AUTH-003: skill:python-patterns-extra: MUST NOT match query python-patterns."""
    data = _make_explain_json(
        hits=[
            {"ref": "repo:other.md:something", "score": 0.9},
            {"ref": "skill:python-patterns-extra:some-chunk", "score": 0.8},
        ],
        expanded_terms=["python-patterns"],
    )

    result = _run_alias_match(data)
    # "skill:python-patterns-extra:" does NOT start with "skill:python-patterns:"
    # because the prefix is f"skill:{term}:" = "skill:python-patterns:"
    # and "skill:python-patterns-extra:" starts with "skill:python-patterns-" NOT "skill:python-patterns:"
    assert result == ""
