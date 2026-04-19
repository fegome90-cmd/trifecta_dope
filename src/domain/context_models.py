"""Domain Models for Trifecta Context."""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ContextChunk(BaseModel):
    """A single chunk of context evidence."""

    id: str = Field(..., description="Stable deterministic ID: doc:sha1(doc+text)[:10]")
    doc: str = Field(..., description="Source document name (skill, agent, etc.)")
    title_path: List[str] = Field(..., description="Hierarchical path to this chunk")
    text: str = Field(..., description="The actual text content")
    char_count: int
    token_est: int
    source_path: str = Field(..., description="Path relative to repo root")
    chunking_method: str = "whole_file"


class ContextIndexEntry(BaseModel):
    """Lightweight entry for search and discovery (L0)."""

    id: str
    title_path_norm: str
    preview: str
    token_est: int


class SourceFile(BaseModel):
    """Metadata about a source file used for the context pack."""

    path: str
    sha256: str
    mtime: float
    chars: int


class ContextPack(BaseModel):
    """The complete context pack (Context Pack v1)."""

    schema_version: int = 1
    segment: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    digest: str = ""
    source_files: List[SourceFile] = Field(default_factory=list)
    chunks: List[ContextChunk]
    index: List[ContextIndexEntry]


class SearchHit(BaseModel):
    """A single search result hit."""

    id: str
    title_path: List[str]
    preview: str
    token_est: int
    source_path: str
    score: float
    score_details: Optional[dict[str, float]] = Field(default=None)


class SearchResult(BaseModel):
    """Result from ctx.search.

    ``authority_state`` carries the ``publication_state`` from the promoted
    set's receipt when the segment uses the ``skill_hub`` indexing policy.
    It is segment metadata by convenience — callers can use it to decide
    whether to trust the corpus or show a warning, but search result
    relevance scoring does not depend on it.

    Values:
        ``"healthy"``  — corpus passed integrity evaluation (or non-skill-hub segment)
        ``"degraded"`` — corpus published with missing required sources
    """

    hits: List[SearchHit]
    authority_state: str = "healthy"


class GetResult(BaseModel):
    """Result from ctx.get."""

    chunks: List[ContextChunk]
    total_tokens: int
    stop_reason: str = Field(
        ..., description="Reason for stopping: complete, budget, max_chunks, evidence"
    )
    chunks_requested: int = Field(..., description="Number of chunk IDs requested")
    chunks_returned: int = Field(..., description="Number of chunks actually returned")
    chars_returned_total: int = Field(..., description="Total characters returned")
    evidence_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Evidence signals: strong_hit, support"
    )
