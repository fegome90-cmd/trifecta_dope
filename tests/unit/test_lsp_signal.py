"""Tests for Oracle LSP signal -- _execute_lsp_signal().

Phase 4 (LSP Intelligence) -- tasks 4.1-4.14:
Covers all 7 LSP signal states plus telemetry and fidelity promotion.

Signal states:
  lsp_not_applicable, lsp_not_injected, lsp_not_ready,
  lsp_timeout, lsp_error, lsp_no_result, lsp_used
"""

from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.application.oracle_use_case import SearchOracleUseCase
from src.application.ast_parser import SymbolInfo, ParseResult
from src.domain.context_models import OracleResult, SearchHit
from src.infrastructure.lsp_client import LSPState


# -- Helpers -------------------------------------------------------------------


def _make_symbol(
    name: str = "resolve_segment_ref",
    start_line: int = 42,
    kind: str = "function",
) -> SymbolInfo:
    """Build a SymbolInfo for AST mocking."""
    return SymbolInfo(
        kind=kind,
        name=name,
        qualified_name=name,
        start_line=start_line,
        end_line=start_line + 5,
        signature_stub=f"def {name}(...)",
    )


def _make_ast_result(symbols: Optional[list[SymbolInfo]] = None) -> MagicMock:
    """Build a mock ParseResult with given symbols."""
    result = MagicMock(spec=ParseResult)
    result.symbols = symbols if symbols is not None else []
    return result


def _make_oracle(
    lsp_client: Optional[Any] = None,
    graph_service: Optional[Any] = None,
    telemetry: Optional[Any] = None,
) -> SearchOracleUseCase:
    """Build SearchOracleUseCase with mocked ast_builder."""
    ast_builder = MagicMock()
    ast_builder.build.return_value = _make_ast_result(symbols=[])
    return SearchOracleUseCase(
        ast_builder=ast_builder,
        lsp_client=lsp_client,
        graph_service=graph_service,
        telemetry=telemetry,
    )


def _mock_lsp(
    state: LSPState = LSPState.READY,
    request_return: Optional[Dict[str, Any]] = None,
    request_side_effect: Optional[Any] = None,
) -> MagicMock:
    """Build mock LSPClient with controlled state and request() return."""
    lsp = MagicMock()
    lsp.state = state
    if request_side_effect is not None:
        lsp.request.side_effect = request_side_effect
    else:
        lsp.request.return_value = request_return
    return lsp


def _run(oracle: SearchOracleUseCase, query: str) -> OracleResult:
    """Run oracle.execute() with ContextService mocked (empty PRIME)."""
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[])
        result_obj = oracle.execute(Path("/tmp/repo"), query)
    return result_obj.unwrap()


def _run_with_hit(
    oracle: SearchOracleUseCase,
    query: str,
    symbol_name: str = "resolve_segment_ref",
    source_path: str = "src/domain/mod.py",
) -> OracleResult:
    """Run oracle.execute() with a PRIME hit and AST symbols for LSP positioning."""
    hit = SearchHit(
        id="test",
        title_path=["main"],
        preview="test",
        token_est=10,
        source_path=source_path,
        score=1.0,
    )

    # Set up ast_builder to return a symbol matching the query target
    sym = _make_symbol(name=symbol_name)
    oracle.ast_builder.build.return_value = _make_ast_result(symbols=[sym])

    # We need the file to "exist" for AST resolution
    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[hit])
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result_obj = oracle.execute(Path("/tmp/repo"), query)
    return result_obj.unwrap()


# -- 4.2: lsp_not_applicable ---------------------------------------------------


def test_lsp_signal_not_applicable():
    """Non-semantic query -> lsp_not_applicable, no request issued."""
    lsp = _mock_lsp(state=LSPState.READY)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run(oracle, "how to configure the daemon")

    assert r.metadata["lsp_signal"] == "lsp_not_applicable"
    assert r.lsp_data is None
    lsp.request.assert_not_called()


# -- 4.3: lsp_not_injected -----------------------------------------------------


def test_lsp_signal_not_injected():
    """No LSP client (None) -> lsp_not_injected."""
    oracle = _make_oracle(lsp_client=None)
    r = _run(oracle, "what is foo")

    assert r.metadata["lsp_signal"] == "lsp_not_injected"
    assert r.lsp_data is None


# -- 4.4: lsp_not_ready (COLD, WARMING) ----------------------------------------


def test_lsp_signal_not_ready_cold():
    """LSPClient state COLD -> lsp_not_ready, no request issued."""
    lsp = _mock_lsp(state=LSPState.COLD)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run(oracle, "what is foo")

    assert r.metadata["lsp_signal"] == "lsp_not_ready"
    assert r.lsp_data is None
    lsp.request.assert_not_called()


def test_lsp_signal_not_ready_warming():
    """LSPClient state WARMING -> lsp_not_ready, no request issued."""
    lsp = _mock_lsp(state=LSPState.WARMING)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run(oracle, "what is foo")

    assert r.metadata["lsp_signal"] == "lsp_not_ready"
    assert r.lsp_data is None
    lsp.request.assert_not_called()


# -- 4.5: lsp_not_ready (FAILED, CLOSED) ---------------------------------------


def test_lsp_signal_not_ready_failed():
    """LSPClient state FAILED -> lsp_not_ready, no request issued."""
    lsp = _mock_lsp(state=LSPState.FAILED)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run(oracle, "what is foo")

    assert r.metadata["lsp_signal"] == "lsp_not_ready"
    assert r.lsp_data is None
    lsp.request.assert_not_called()


def test_lsp_signal_not_ready_closed():
    """LSPClient state CLOSED -> lsp_not_ready, no request issued."""
    lsp = _mock_lsp(state=LSPState.CLOSED)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run(oracle, "what is foo")

    assert r.metadata["lsp_signal"] == "lsp_not_ready"
    assert r.lsp_data is None
    lsp.request.assert_not_called()


# -- 4.6: lsp_timeout ----------------------------------------------------------


def test_lsp_signal_timeout():
    """LSP request exceeding budget -> lsp_timeout (deterministic: budget set to 0ms)."""
    lsp = _mock_lsp(
        state=LSPState.READY,
        request_return={"contents": [{"language": "python", "value": "def foo()"}]},
    )
    oracle = _make_oracle(lsp_client=lsp)

    # Set budget to 0ms so any real elapsed time exceeds it — no sleep needed
    with patch("src.application.oracle_use_case._LSP_BUDGET_MS", 0.0):
        r = _run_with_hit(oracle, "what is resolve_segment_ref")

    assert r.metadata["lsp_signal"] == "lsp_timeout"
    assert r.lsp_data is None


# -- 4.7: lsp_error ------------------------------------------------------------


def test_lsp_signal_error():
    """LSP returns error dict -> lsp_error."""
    lsp = _mock_lsp(
        state=LSPState.READY,
        request_return={"__lsp_error__": True, "error": {"code": -32600}},
    )
    oracle = _make_oracle(lsp_client=lsp)
    r = _run_with_hit(oracle, "what is resolve_segment_ref")

    assert r.metadata["lsp_signal"] == "lsp_error"
    assert r.lsp_data is None


# -- 4.8: lsp_no_result (empty/null response) ----------------------------------


def test_lsp_signal_no_result():
    """LSP returns empty/null contents -> lsp_no_result."""
    lsp = _mock_lsp(
        state=LSPState.READY,
        request_return={"contents": None},
    )
    oracle = _make_oracle(lsp_client=lsp)
    r = _run_with_hit(oracle, "what is resolve_segment_ref")

    assert r.metadata["lsp_signal"] == "lsp_no_result"
    assert r.lsp_data is None


# -- 4.9: lsp_used (successful hover) ------------------------------------------


def test_lsp_signal_used_hover():
    """Successful hover -> lsp_used with populated lsp_data."""
    hover_result = {
        "contents": [
            {"language": "python", "value": "def resolve_segment_ref(path: Path) -> SegmentRef"},
            {"kind": "plaintext", "value": "Resolves segment reference from path."},
        ],
    }
    lsp = _mock_lsp(state=LSPState.READY, request_return=hover_result)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run_with_hit(oracle, "what is resolve_segment_ref")

    assert r.metadata["lsp_signal"] == "lsp_used"
    assert r.lsp_data is not None
    assert r.lsp_data["method"] == "hover"
    assert r.lsp_data["target"] == "resolve_segment_ref"
    assert r.lsp_data["contents"] == hover_result["contents"]
    assert "latency_ms" in r.lsp_data


# -- 4.10: lsp_used with ES query ----------------------------------------------


def test_lsp_signal_es_query():
    """Spanish query 'que es resolve_segment_ref' -> lsp_used."""
    hover_result = {
        "contents": [
            {"language": "python", "value": "def resolve_segment_ref(path: Path) -> SegmentRef"},
        ],
    }
    lsp = _mock_lsp(state=LSPState.READY, request_return=hover_result)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run_with_hit(oracle, "que es resolve_segment_ref")

    assert r.metadata["lsp_signal"] == "lsp_used"


# -- 4.11: AST has no matching symbol ------------------------------------------


def test_lsp_signal_ast_no_symbol_match():
    """AST returns no matching symbol for the target -> lsp_no_result, no request."""
    lsp = _mock_lsp(state=LSPState.READY)
    oracle = _make_oracle(lsp_client=lsp)

    # Provide a hit with AST symbols, but none matching the query target
    hit = SearchHit(
        id="test", title_path=["main"], preview="test",
        token_est=10, source_path="src/domain/mod.py", score=1.0,
    )
    # AST has symbols but none named "resolve_segment_ref"
    other_sym = _make_symbol(name="other_function", start_line=10)
    oracle.ast_builder.build.return_value = _make_ast_result(symbols=[other_sym])

    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[hit])
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result_obj = oracle.execute(Path("/tmp/repo"), "what is resolve_segment_ref")
    r = result_obj.unwrap()

    assert r.metadata["lsp_signal"] == "lsp_no_result"
    assert r.lsp_data is None
    # Critical: no LSP request issued when AST cannot resolve position
    lsp.request.assert_not_called()


# -- 4.12: AST finds symbol at multiple positions -------------------------------


def test_lsp_signal_ast_multiple_match():
    """AST finds symbol at multiple positions -> first match used for hover."""
    hover_result = {
        "contents": [{"language": "python", "value": "def foo() -> str"}],
    }
    lsp = _mock_lsp(state=LSPState.READY, request_return=hover_result)
    oracle = _make_oracle(lsp_client=lsp)

    hit = SearchHit(
        id="test", title_path=["main"], preview="test",
        token_est=10, source_path="src/domain/mod.py", score=1.0,
    )
    sym1 = _make_symbol(name="foo", start_line=10)
    sym2 = _make_symbol(name="foo", start_line=50)
    oracle.ast_builder.build.return_value = _make_ast_result(symbols=[sym1, sym2])

    with patch("src.application.oracle_use_case.ContextService") as MockCS:
        MockCS.return_value.search.return_value = MagicMock(hits=[hit])
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result_obj = oracle.execute(Path("/tmp/repo"), "what is foo")
    r = result_obj.unwrap()

    assert r.metadata["lsp_signal"] == "lsp_used"
    assert r.lsp_data is not None
    # First match (line 10) should be used (LSP uses 0-based lines: 10-1=9)
    lsp.request.assert_called_once()
    call_args = lsp.request.call_args
    position = call_args[0][1]["position"]
    assert position["line"] == 9  # line 10 - 1 = 0-based index 9


# -- 4.13: Telemetry records lsp_signal ----------------------------------------


def test_lsp_signal_telemetry_recorded():
    """Telemetry event MUST include lsp_signal and lsp_signal_ms."""
    mock_telemetry = MagicMock()
    lsp = _mock_lsp(state=LSPState.READY)
    oracle = _make_oracle(lsp_client=lsp, telemetry=mock_telemetry)
    _run(oracle, "how to configure the daemon")

    mock_telemetry.event.assert_called_once()
    call_kwargs = mock_telemetry.event.call_args
    result = call_kwargs[1]["result"] if "result" in call_kwargs[1] else call_kwargs[0][2]
    assert "lsp_signal" in result
    assert "lsp_signal_ms" in result
    assert isinstance(result["lsp_signal_ms"], int)


# -- 4.14: Fidelity promotion --------------------------------------------------


def test_lsp_signal_fidelity_promotion_full():
    """LSP used -> fidelity == 'full'."""
    hover_result = {
        "contents": [{"language": "python", "value": "def resolve_segment_ref(...)"}],
    }
    lsp = _mock_lsp(state=LSPState.READY, request_return=hover_result)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run_with_hit(oracle, "what is resolve_segment_ref")

    assert r.fidelity == "full"
    assert r.metadata["lsp_signal"] == "lsp_used"


def test_lsp_signal_fidelity_promotion_degraded():
    """LSP unavailable + AST available -> fidelity == 'degraded'."""
    lsp = _mock_lsp(state=LSPState.FAILED)
    oracle = _make_oracle(lsp_client=lsp)
    r = _run_with_hit(oracle, "what is resolve_segment_ref")

    assert r.fidelity == "degraded"
    assert r.metadata["lsp_signal"] == "lsp_not_ready"


def test_lsp_signal_fidelity_promotion_fallback():
    """PRIME only (no AST symbols, no LSP) -> fidelity == 'fallback'."""
    oracle = _make_oracle(lsp_client=None)
    r = _run(oracle, "how to configure the daemon")

    assert r.fidelity == "fallback"
