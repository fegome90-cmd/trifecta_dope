"""Unit tests for Agnostic Ranking Heuristics (SH-RANKING-001)."""

import math
import pytest
from pathlib import Path
from src.application.context_service import ContextService
from src.domain.context_models import ContextPack, ContextChunk, ContextIndexEntry

def test_length_normalization_penalizes_noise():
    """Verify that a short precise file beats a long noisy file."""
    chunks = [
        ContextChunk(
            id="skill:noisy", doc="skill", title_path=["other.md"],
            text="testing " * 10, char_count=1000, token_est=1000, source_path="n.md"
        ),
        ContextChunk(
            id="skill:precise", doc="skill", title_path=["other.md"],
            text="testing " * 2, char_count=100, token_est=50, source_path="p.md"
        )
    ]
    index = [
        ContextIndexEntry(id="skill:noisy", title_path_norm="other.md", preview="", token_est=1000),
        ContextIndexEntry(id="skill:precise", title_path_norm="other.md", preview="", token_est=50)
    ]
    pack = ContextPack(segment="test", chunks=chunks, index=index)
    
    service = ContextService(Path("."))
    service._load_pack = lambda: (pack, "healthy")
    
    result = service.search("testing", k=2)
    hits = result.hits
    
    # Precise should win despite having fewer matches (2 vs 10) 
    # because of the lower length penalty.
    assert hits[0].id == "skill:precise"
    assert "length_penalty" in hits[0].score_details

def test_identity_dominates_body_matches():
    """Verify that title matches beat body-only matches."""
    chunks = [
        ContextChunk(
            id="skill:match-title", doc="skill", title_path=["git.md"],
            text="nothing", char_count=10, token_est=10, source_path="g.md"
        ),
        ContextChunk(
            id="skill:noisy-body", doc="skill", title_path=["other.md"],
            text="git " * 20, char_count=1000, token_est=1000, source_path="o.md"
        )
    ]
    index = [
        ContextIndexEntry(id="skill:match-title", title_path_norm="git.md", preview="", token_est=10),
        ContextIndexEntry(id="skill:noisy-body", title_path_norm="other.md", preview="", token_est=1000)
    ]
    pack = ContextPack(segment="test", chunks=chunks, index=index)
    
    service = ContextService(Path("."))
    service._load_pack = lambda: (pack, "healthy")
    
    result = service.search("git", k=2)
    
    # Title match MUST be Top 1
    assert result.hits[0].id == "skill:match-title"
    assert result.hits[0].score_details["identity_score"] >= 4.0
