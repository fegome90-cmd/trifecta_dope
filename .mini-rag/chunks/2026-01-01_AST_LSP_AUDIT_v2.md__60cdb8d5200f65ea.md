### 1. AST Skeleton Map (Tree-sitter)

**Module:** `src/infrastructure/ast_lsp.py`

```python
# Pseudocode structure (v0 minimal)
class SkeletonMapBuilder:
    """Extract structure-only AST for Python."""

    @staticmethod
    def parse_python(code: str) -> SkeletonMap:
        """Parse Python code, extract functions/classes/signatures only."""
        # Uses tree-sitter-python binary (installed via pip)
        # Returns: SkeletonMap(functions=[...], classes=[...])

    @staticmethod
    def compute_structural_hash(skeleton: SkeletonMap) -> str:
        """Hash signature-only, not implementation."""
        # hash(f"fn:{name}:{params}:{return_type}")
        # If body changes but signature doesn't, hash == old
```

**Installation:**
```bash
pip install tree-sitter tree-sitter-python
```

**Why Tree-sitter:**
- **Zero external deps**: C bindings + Python wrapper, ~2MB footprint
- **Parse latency**: <50ms per file (vs Pyright 2-5s cold start)
- **Error recovery**: Parses incomplete code (crucial for agent workflows)

**Performance Target:**
- Single file parse: <50ms
- Repo skeleton (5k files): <5s async
- Cache hit rate: >85%

---
