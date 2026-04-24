"""Tests for query_classifier — relational predicate detection (EN+ES)."""

import pytest

from src.domain.query_classifier import RelationalPredicate, QueryClass, classify_query


class TestClassifyQueryCallers:
    """Caller predicate detection in EN and ES."""

    def test_callers_en_who_calls(self) -> None:
        result = classify_query("who calls SearchOracleUseCase.execute")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "SearchOracleUseCase.execute"

    def test_callers_en_callers_of(self) -> None:
        result = classify_query("callers of execute")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "execute"

    def test_callers_es_quien_llama_a(self) -> None:
        result = classify_query("quién llama a ContextService.search")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "ContextService.search"

    def test_callers_es_quien_llama_al(self) -> None:
        result = classify_query("quién llama al GraphStore")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "GraphStore"

    def test_callers_es_quienes_llaman_a(self) -> None:
        result = classify_query("quienes llaman a execute")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "execute"


class TestClassifyQueryCallees:
    """Callee predicate detection in EN and ES."""

    def test_callees_en_what_does_call(self) -> None:
        result = classify_query("what does ContextService call")
        assert result.predicate is not None
        assert result.predicate.relation == "callees"
        assert result.predicate.target == "ContextService"

    def test_callees_en_callees_of(self) -> None:
        result = classify_query("callees of SearchOracleUseCase")
        assert result.predicate is not None
        assert result.predicate.relation == "callees"
        assert result.predicate.target == "SearchOracleUseCase"

    def test_callees_es_que_llama(self) -> None:
        result = classify_query("qué llama GraphService")
        assert result.predicate is not None
        assert result.predicate.relation == "callees"
        assert result.predicate.target == "GraphService"

    def test_callees_es_que_llaman(self) -> None:
        result = classify_query("qué llaman a execute")
        assert result.predicate is not None
        assert result.predicate.relation == "callees"
        assert result.predicate.target == "execute"


class TestClassifyQueryNoPredicate:
    """Non-relational queries must return no predicate."""

    @pytest.mark.parametrize(
        "query",
        [
            "how to configure the daemon",
            "what is context_pack.json",
            "show me the skill hub index",
            "context service",  # ambiguous — no relational structure
            "explain the oracle architecture",
        ],
    )
    def test_no_predicate(self, query: str) -> None:
        result = classify_query(query)
        assert result.predicate is None


class TestClassifyQueryEdgeCases:
    """Edge cases: empty, malformed, incomplete."""

    def test_empty_string(self) -> None:
        result = classify_query("")
        assert result.predicate is None

    def test_who_calls_no_target(self) -> None:
        result = classify_query("who calls")
        assert result.predicate is None

    def test_quien_llama_a_no_target(self) -> None:
        result = classify_query("quién llama a")
        assert result.predicate is None

    def test_target_with_trailing_whitespace(self) -> None:
        result = classify_query("who calls  execute  ")
        assert result.predicate is not None
        assert result.predicate.target == "execute"

    def test_target_with_dots_and_underscores(self) -> None:
        result = classify_query("callers of module.submodule.MyClass.method")
        assert result.predicate is not None
        assert result.predicate.target == "module.submodule.MyClass.method"

    def test_a_la_contraction(self) -> None:
        result = classify_query("quién llama a la ContextService")
        assert result.predicate is not None
        assert result.predicate.relation == "callers"
        assert result.predicate.target == "ContextService"
