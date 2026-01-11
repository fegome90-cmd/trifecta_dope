### 3.3 AST Parser

**Ubicación**: `src/application/ast_parser.py`

**Estado Actual**: Implementación simplificada (stub)

```python
class ASTParser:
    def parse(self, file_path: Path) -> Tuple[List[ChildSymbol], str]:
        content = file_path.read_text(errors="replace")
        sha8 = hashlib.sha256(content.encode()).hexdigest()[:8]

        # Fake children para demostración
        children = [
            ChildSymbol(
                name="example_func",
                kind="function",
                range=Range(start_line=1, end_line=10),
                signature_stub="def example_func():",
            ),
        ]
        return children, sha8
```

**Nota**: El código indica que tree-sitter fue usado en "Phase 2a" pero fue simplificado para "restoration risk management".
