"""Chunking logic for Context Pack MVP.

Whole-file chunking strategy:
- Treats each doc as a single chunk
- Stable IDs via SHA256 content hashing
- Token estimation: len(text) // 4
"""

import hashlib
from src.domain.models import Chunk


def chunk_whole_file(doc_name: str, content: str) -> Chunk:
    """Create a single chunk from entire file content.

    Args:
        doc_name: Name of the document (e.g., "skill", "agent", "prime")
        content: Full file content

    Returns:
        Chunk with stable ID, title=doc_name, full text, and token estimate

    Contract:
        - ID format: {doc_name}:{sha256(content)[:10]}
        - Title: doc_name
        - Text: unchanged content
        - Token estimate: len(content) // 4 (rounds down)
    """
    # Generate stable content-addressed ID
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:10]
    chunk_id = f"{doc_name}:{content_hash}"

    # Token estimation (1 token ≈ 4 chars)
    token_est = len(content) // 4

    return Chunk(
        id=chunk_id,
        doc=doc_name,
        title=doc_name,
        text=content,
        token_est=token_est,
    )
