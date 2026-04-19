"""Unit tests for Trifecta Context Models (SH-RANKING-001)."""

import json
import pytest
from src.domain.context_models import SearchHit

def test_search_hit_serialization_with_score_details():
    """Verify SearchHit handles score_details dictionary."""
    details = {
        "identity": 2.0,
        "body_raw": 1.0,
        "norm_factor": 1.5,
        "body_norm": 0.66
    }
    hit = SearchHit(
        id="skill:test",
        title_path=["test.md"],
        preview="...",
        token_est=100,
        source_path="test.md",
        score=2.66,
        score_details=details
    )
    
    # Test object access
    assert hit.score_details == details
    
    # Test Pydantic JSON serialization
    data = json.loads(hit.model_dump_json())
    assert "score_details" in data
    assert data["score_details"]["identity"] == 2.0

def test_search_hit_works_without_details():
    """Verify backward compatibility for legacy hits."""
    hit = SearchHit(
        id="skill:test",
        title_path=["test.md"],
        preview="...",
        token_est=100,
        source_path="test.md",
        score=1.5
    )
    assert hit.score_details is None
    
    data = json.loads(hit.model_dump_json())
    assert data["score_details"] is None
