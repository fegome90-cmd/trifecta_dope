import ast
from pathlib import Path


GRAPH_NAMESPACE_FILES = (
    Path("src/application/graph_indexer.py"),
    Path("src/application/graph_service.py"),
    Path("src/domain/graph_models.py"),
    Path("src/infrastructure/cli_graph.py"),
    Path("src/infrastructure/graph_store.py"),
)


def test_graph_namespace_does_not_import_segment_ref_v2() -> None:
    banned_module = "src.trifecta.domain.segment_ref"

    for file_path in GRAPH_NAMESPACE_FILES:
        tree = ast.parse(file_path.read_text(), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == banned_module:
                raise AssertionError(f"{file_path} imports banned module {banned_module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == banned_module:
                        raise AssertionError(f"{file_path} imports banned module {banned_module}")
