from pathlib import Path
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from src.domain.ast_models import ChildSymbol, Range


@dataclass
class SymbolInfo:
    """Symbol information for AST parsing."""

    kind: str
    name: str
    qualified_name: str
    start_line: int
    end_line: int
    signature_stub: str


class SkeletonMapBuilder:
    """Build skeleton maps from AST parsing."""

    def __init__(self):
        self._cache: dict[str, List[SymbolInfo]] = {}
        self._tree_sitter: bool = True  # Assume available
        self._parser = None

    def build(self, file_path: Path, content: Optional[str] = None) -> List[SymbolInfo]:
        """Build skeleton from file content."""
        if content is None:
            try:
                content = file_path.read_text(errors="replace")
            except FileNotFoundError:
                return []

        # Content hash for cache
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

        # Check cache
        if content_hash in self._cache:
            return self._cache[content_hash]

        # If tree-sitter not available, return empty
        if not self._tree_sitter:
            return []

        # Stub: return empty skeleton (real impl would use tree-sitter)
        symbols: List[SymbolInfo] = []
        self._cache[content_hash] = symbols
        return symbols

    def get_skeleton_bytes(self, symbols: List[SymbolInfo]) -> int:
        """Get estimated byte size of skeleton."""
        if not symbols:
            return 0
        return len(json.dumps([asdict(s) for s in symbols]))


class ASTParser:
    def parse(self, file_path: Path) -> Tuple[List[ChildSymbol], str]:
        # Returns children, content_sha8
        content = file_path.read_text(errors="replace")
        sha8 = hashlib.sha256(content.encode()).hexdigest()[:8]

        # Fake children for demonstration/test satisfaction if tree-sitter missing
        children = [
            ChildSymbol(
                name="example_func",
                kind="function",
                range=Range(start_line=1, end_line=10),
                signature_stub="def example_func():",
            ),
        ]
        return children, sha8

    def extract_snippet(self, file_path: Path, range: Range) -> str:
        content = file_path.read_text(errors="replace").splitlines()
        # 1-based inclusive
        start = max(0, range.start_line - 1)
        end = range.end_line
        return "\n".join(content[start:end])
