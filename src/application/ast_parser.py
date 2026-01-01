"""
AST Parser Layer: Python skeleton extraction with tree-sitter.

DESIGN CONSTRAINTS:
- Content-addressed caching: SHA256(content) → skeleton
- Telemetry: ast.parse, ast.cache_hit, ast.cache_miss events
- No file I/O beyond reading content once
- Skeleton = list[SymbolInfo]: kind, name, qualified_name, start_line, end_line, signature_stub
- Privacy: no absolute paths logged, only relative + hashes
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any

__all__ = [
    "SymbolInfo",
    "SkeletonMapBuilder",
]


@dataclass(frozen=True)
class SymbolInfo:
    """Symbol extracted from AST."""

    kind: str  # "class", "function", "module", "import"
    name: str  # simple name
    qualified_name: str  # e.g. "MyClass.method"
    start_line: int  # 0-indexed
    end_line: int
    signature_stub: str  # e.g. "def method(a: int) -> str:"


if TYPE_CHECKING:
    from tree_sitter import Parser as TS_Parser  # type: ignore[import-not-found]
else:
    TS_Parser = Any  # type: ignore[misc]


class SkeletonMapBuilder:
    """
    Builds Python AST skeletons with content-based caching.

    Cache key = SHA256(content), value = list[SymbolInfo]
    """

    def __init__(self) -> None:
        """Initialize skeleton cache."""
        self._cache: dict[str, list[SymbolInfo]] = {}
        # Lazy import to avoid hard dep
        self._tree_sitter_available: bool = False
        # Runtime attribute (may remain None if parser unavailable)
        self._parser: TS_Parser | None = None

    def _ensure_parser(self) -> None:
        """Lazy-load tree-sitter parser (fail gracefully if not available)."""
        if self._parser is not None:
            return

        try:
            from importlib import import_module

            ts = import_module("tree_sitter")
            Language = getattr(ts, "Language")
            Parser = getattr(ts, "Parser")

            python_lang = Language("~/.cache/tree-sitter/tree-sitter-python.so")
            parser = Parser()
            parser.set_language(python_lang)
            self._parser = parser
            self._tree_sitter_available = True
        except Exception:
            # Fail gracefully: AST parsing disabled
            self._tree_sitter_available = False
            self._parser = None

    def build(self, file_path: Path, content: str) -> list[SymbolInfo]:
        """
        Extract Python skeleton (list of symbols).

        Returns cached result if content matches SHA256.
        Side effects: populates cache, emits telemetry (caller responsible).

        Args:
            file_path: For logging only (not used for caching)
            content: Source code to parse

        Returns:
            List of SymbolInfo (empty if parsing fails)
        """
        # Content-addressed cache key
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cache_key = content_hash[:16]  # 16 chars = 64 bits collision-resistant

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Parse
        self._ensure_parser()
        parser = self._parser
        if not self._tree_sitter_available or parser is None:
            # Parser not available: return empty skeleton
            return []

        try:
            tree = parser.parse(content.encode())
            symbols = self._extract_symbols(tree.root_node, content, "")
            self._cache[cache_key] = symbols
            return symbols
        except Exception:
            # Parsing failed: return empty skeleton
            return []

    def _extract_symbols(
        self,
        node: object,
        content: str,
        parent_qualified: str,
    ) -> list[SymbolInfo]:
        """
        Recursively extract symbols from AST node.

        Args:
            node: tree-sitter Node
            content: Source code (for signature extraction)
            parent_qualified: Qualified name of parent scope

        Returns:
            List of SymbolInfo extracted from this node and children
        """
        symbols: list[SymbolInfo] = []

        # Early exit if tree-sitter not loaded
        if not hasattr(node, "type"):
            return symbols

        node_any: Any = node
        node_type = getattr(node_any, "type", None)

        # Module-level definitions
        if node_type == "function_definition":
            name = self._get_node_child_text(node_any, "name")
            if name:
                qualified = (
                    f"{parent_qualified}.{name}"
                    if parent_qualified
                    else name
                )
                sig = self._get_signature_stub(node_any, content)
                symbols.append(
                    SymbolInfo(
                        kind="function",
                        name=name,
                        qualified_name=qualified,
                        start_line=node_any.start_point[0],
                        end_line=node_any.end_point[0],
                        signature_stub=sig,
                    )
                )

        elif node_type == "class_definition":
            name = self._get_node_child_text(node_any, "name")
            if name:
                qualified = (
                    f"{parent_qualified}.{name}"
                    if parent_qualified
                    else name
                )
                sig = self._get_signature_stub(node_any, content)
                symbols.append(
                    SymbolInfo(
                        kind="class",
                        name=name,
                        qualified_name=qualified,
                        start_line=node_any.start_point[0],
                        end_line=node_any.end_point[0],
                        signature_stub=sig,
                    )
                )

                # Recursively extract methods/nested classes
                for child in getattr(node_any, "children", []):
                    child_type = getattr(child, "type", None)
                    if child_type in ("function_definition", "class_definition"):
                        child_symbols = self._extract_symbols(
                            child, content, qualified
                        )
                        symbols.extend(child_symbols)

        elif node_type == "module":
            # Traverse module children
            for child in getattr(node_any, "children", []):
                child_symbols = self._extract_symbols(child, content, "")
                symbols.extend(child_symbols)

        return symbols

    def _get_node_child_text(self, node: object, field_name: str) -> Optional[str]:
        """Get text of named child node."""
        try:
            child = node.child_by_field_name(field_name)  # type: ignore
            if child:
                return child.text.decode()  # type: ignore
        except Exception:
            pass
        return None

    def _get_signature_stub(self, node: object, content: str) -> str:
        """Extract signature line (first line of definition)."""
        try:
            start_byte = node.start_byte  # type: ignore
            # Find colon (end of signature)
            colon_pos = content.find(":", start_byte)
            if colon_pos > start_byte:
                return content[start_byte:colon_pos].strip() + ":"
        except Exception:
            pass
        return "..."

    def get_skeleton_bytes(self, symbols: list[SymbolInfo]) -> int:
        """Estimate bytes for skeleton (for telemetry)."""
        return len(json.dumps([asdict(s) for s in symbols]))
