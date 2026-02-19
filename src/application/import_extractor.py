"""Import extractor using stdlib AST."""

import ast
from src.domain.discovery_models import ImportInfo, ExtractionResult


class ImportExtractor(ast.NodeVisitor):
    """AST visitor that extracts import statements."""

    def __init__(self) -> None:
        self.imports: list[ImportInfo] = []
        self.warnings: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    name=alias.name,
                    is_relative=False,
                    level=0,
                    imported_names=(),
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "__builtins__":
            return

        imported_names = tuple(alias.name for alias in node.names)

        self.imports.append(
            ImportInfo(
                name=node.module or "",
                is_relative=node.level > 0,
                level=node.level,
                imported_names=imported_names,
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
            self.warnings.append(f"Dynamic import detected at line {node.lineno}")
        self.generic_visit(node)


def extract_imports(source: str) -> ExtractionResult:
    """Extract import statements from Python source code.

    Args:
        source: Python source code as string.

    Returns:
        ExtractionResult containing all imports and warnings.
    """
    if not source:
        return ExtractionResult(imports=(), line_count=0, warnings=())

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ExtractionResult(imports=(), line_count=0, warnings=("Syntax error in source",))

    extractor = ImportExtractor()
    extractor.visit(tree)

    return ExtractionResult(
        imports=tuple(extractor.imports),
        line_count=len(source.splitlines()),
        warnings=tuple(extractor.warnings),
    )
