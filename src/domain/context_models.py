"""Domain Models for Trifecta Context."""
from datetime import datetime
from typing import Literal, Optional, List, Dict
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


class SearchResult(BaseModel):
    """Result from ctx.search."""
    hits: List[SearchHit]


class GetResult(BaseModel):
    """Result from ctx.get."""
    chunks: List[ContextChunk]
    total_tokens: int
