"""Tests for semantic predicate detection in query_classifier.

Phase 1 (LSP Intelligence) — tasks 1.1–1.6:
- EN patterns: "what is X", "show me X"
- ES patterns: "qué es X", "mostrame X"
- Non-semantic queries return semantic=None
- Mixed relational+semantic returns both populated
- Edge cases: empty target, very long target, unicode target
"""

import pytest

from src.domain.query_classifier import (
    QueryClass,
    SemanticPredicate,
    classify_query,
)


# ── EN patterns ──────────────────────────────────────────────────────────────


class TestEnSemanticPatterns:
    """English semantic predicate detection."""

    def test_what_is_extracts_target(self) -> None:
        result = classify_query("what is resolve_segment_ref")
        assert result.semantic is not None
        assert result.semantic.method == "hover"
        assert result.semantic.target == "resolve_segment_ref"

    def test_what_is_case_insensitive(self) -> None:
        result = classify_query("What Is MyClass")
        assert result.semantic is not None
        assert result.semantic.target == "MyClass"

    def test_what_is_with_leading_whitespace(self) -> None:
        result = classify_query("  what is foo")
        assert result.semantic is not None
        assert result.semantic.target == "foo"

    def test_show_me_extracts_target(self) -> None:
        result = classify_query("show me SearchOracleUseCase")
        assert result.semantic is not None
        assert result.semantic.method == "hover"
        assert result.semantic.target == "SearchOracleUseCase"

    def test_show_me_case_insensitive(self) -> None:
        result = classify_query("Show Me bar_func")
        assert result.semantic is not None
        assert result.semantic.target == "bar_func"

    def test_what_is_mid_sentence(self) -> None:
        """Pattern should match via search(), not just anchored."""
        result = classify_query("please tell me what is MyClass")
        assert result.semantic is not None
        assert result.semantic.target == "MyClass"


# ── ES patterns ──────────────────────────────────────────────────────────────


class TestEsSemanticPatterns:
    """Spanish semantic predicate detection."""

    def test_que_es_extracts_target(self) -> None:
        result = classify_query("que es resolve_segment_ref")
        assert result.semantic is not None
        assert result.semantic.method == "hover"
        assert result.semantic.target == "resolve_segment_ref"

    def test_que_es_with_accent(self) -> None:
        result = classify_query("qué es SearchOracleUseCase")
        assert result.semantic is not None
        assert result.semantic.target == "SearchOracleUseCase"

    def test_mostrame_extracts_target(self) -> None:
        result = classify_query("mostrame foo_func")
        assert result.semantic is not None
        assert result.semantic.method == "hover"
        assert result.semantic.target == "foo_func"

    def test_que_es_case_insensitive(self) -> None:
        result = classify_query("Que Es BarClass")
        assert result.semantic is not None
        assert result.semantic.target == "BarClass"

    def test_mostrame_case_insensitive(self) -> None:
        result = classify_query("Mostrame MyClass")
        assert result.semantic is not None
        assert result.semantic.target == "MyClass"


# ── Non-semantic queries ─────────────────────────────────────────────────────


class TestNonSemanticQueries:
    """Queries without semantic predicates must return semantic=None."""

    def test_configure_daemon(self) -> None:
        result = classify_query("how to configure the daemon")
        assert result.semantic is None
        assert result.predicate is None

    def test_como_configurar_daemon(self) -> None:
        result = classify_query("como configurar el daemon")
        assert result.semantic is None

    def test_empty_query(self) -> None:
        result = classify_query("")
        assert result.semantic is None
        assert result.predicate is None

    def test_whitespace_only_query(self) -> None:
        result = classify_query("   ")
        assert result.semantic is None
        assert result.predicate is None

    def test_random_sentence(self) -> None:
        result = classify_query("the quick brown fox jumps over the lazy dog")
        assert result.semantic is None


# ── Mixed relational + semantic ──────────────────────────────────────────────


class TestMixedRelationalSemantic:
    """A query can have both relational and semantic predicates."""

    def test_what_is_x_and_who_calls_y(self) -> None:
        result = classify_query("what is foo and who calls bar")
        assert result.semantic is not None
        assert result.semantic.target == "foo"
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "bar"

    def test_who_calls_x_returns_no_semantic(self) -> None:
        """'who calls foo' is relational-only, not semantic."""
        result = classify_query("who calls foo")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.semantic is None

    def test_show_me_x_is_semantic_only(self) -> None:
        result = classify_query("show me foo")
        assert result.semantic is not None
        assert result.semantic.target == "foo"
        assert result.predicate is None


# ── Edge cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases: empty target, very long target, unicode target."""

    def test_what_is_with_trailing_whitespace_target(self) -> None:
        result = classify_query("what is foo   ")
        assert result.semantic is not None
        assert result.semantic.target == "foo"

    def test_very_long_target(self) -> None:
        long_name = "a" * 200
        result = classify_query(f"what is {long_name}")
        assert result.semantic is not None
        assert result.semantic.target == long_name

    def test_unicode_target(self) -> None:
        result = classify_query("what is funcion_n")
        assert result.semantic is not None
        assert result.semantic.target == "funcion_n"

    def test_underscore_target(self) -> None:
        result = classify_query("what is _private_method")
        assert result.semantic is not None
        assert result.semantic.target == "_private_method"

    def test_dotted_target_captures_first_token(self) -> None:
        r"""Regex captures \S+, so dotted names are captured fully."""
        result = classify_query("what is module.ClassName")
        assert result.semantic is not None
        assert result.semantic.target == "module.ClassName"

    def test_predicate_is_frozen(self) -> None:
        """SemanticPredicate must be immutable."""
        sp = SemanticPredicate(method="hover", target="foo")
        with pytest.raises(AttributeError):
            sp.target = "bar"  # type: ignore[misc]

    def test_query_class_is_frozen(self) -> None:
        """QueryClass must be immutable."""
        qc = QueryClass(predicate=None, semantic=None)
        with pytest.raises(AttributeError):
            qc.semantic = SemanticPredicate(method="hover", target="x")  # type: ignore[misc]
