"""Tests for OracleResult — graph_data field addition."""

import json
from src.domain.context_models import OracleResult, SearchHit


def test_oracle_result_accepts_graph_data_none():
    """OracleResult must accept graph_data as None (default)."""
    result = OracleResult(
        fidelity="fallback",
        ast_symbols=[],
        prime_chunks=[],
        metadata={},
    )
    assert result.graph_data is None


def test_oracle_result_accepts_graph_data_populated():
    """OracleResult must accept graph_data with caller nodes."""
    graph = {
        "relation": "callers",
        "target": "execute",
        "nodes": [
            {"symbol_name": "cli_main", "qualified_name": "cli.cli_main", "file_rel": "src/infrastructure/cli.py", "line": 42, "kind": "function"}
        ],
        "latency_ms": 8,
    }
    result = OracleResult(
        fidelity="degraded",
        ast_symbols=["execute"],
        prime_chunks=[],
        graph_data=graph,
        metadata={"graph_signal": "used"},
    )
    assert result.graph_data is not None
    assert result.graph_data["relation"] == "callers"
    assert len(result.graph_data["nodes"]) == 1
    assert result.graph_data["nodes"][0]["symbol_name"] == "cli_main"


def test_oracle_result_serializes_graph_data():
    """graph_data must survive JSON round-trip."""
    graph = {"relation": "callees", "target": "search", "nodes": [], "latency_ms": 3}
    result = OracleResult(
        fidelity="fallback",
        graph_data=graph,
        prime_chunks=[],
        metadata={},
    )
    data = json.loads(result.model_dump_json())
    assert data["graph_data"]["relation"] == "callees"
    assert data["graph_data"]["nodes"] == []


def test_oracle_result_backward_compatible_without_graph_data():
    """Existing code that doesn't pass graph_data must still work."""
    result = OracleResult(
        fidelity="fallback",
        prime_chunks=[
            SearchHit(
                id="test:1",
                title_path=["test.md"],
                preview="hello",
                token_est=10,
                source_path="test.md",
                score=1.0,
            )
        ],
        metadata={"latency_ms": 13},
    )
    assert result.graph_data is None
    assert len(result.prime_chunks) == 1
