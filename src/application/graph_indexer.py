import ast as ast_module
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.application.ast_parser import SkeletonMapBuilder
from src.domain.graph_models import (
    GraphEdge,
    GraphIndexSummary,
    GraphNode,
    make_edge_id,
    make_node_id,
)
from src.domain.segment_resolver import resolve_segment_ref
from src.infrastructure.graph_store import GraphStore


@dataclass(frozen=True)
class _FileGraphData:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class _DirectCallCollector(ast_module.NodeVisitor):
    def __init__(self) -> None:
        self.call_names: list[str] = []

    def visit_Call(self, node: ast_module.Call) -> None:
        if isinstance(node.func, ast_module.Name):
            self.call_names.append(node.func.id)
        return None

    def visit_FunctionDef(self, node: ast_module.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast_module.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast_module.ClassDef) -> None:
        return None

    def visit_Lambda(self, node: ast_module.Lambda) -> None:
        return None


class GraphIndexer:
    def __init__(self, store: GraphStore | None = None) -> None:
        self._store = store

    def index_segment(self, segment: Path | str) -> GraphIndexSummary:
        segment_ref = resolve_segment_ref(segment)
        segment_root = segment_ref.root_abs
        store = self._store or GraphStore(
            GraphStore.db_path_for_segment(segment_root, segment_ref.id),
            segment_id=segment_ref.id,
        )
        builder = SkeletonMapBuilder(segment_id=str(segment_root))
        indexed_at = datetime.now(timezone.utc).isoformat()

        all_nodes: list[GraphNode] = []
        all_edges: list[GraphEdge] = []
        source_root = segment_root / "src"

        if source_root.exists():
            for file_path in sorted(source_root.rglob("*.py")):
                file_data = self._index_file(segment_ref.id, segment_root, file_path, builder)
                all_nodes.extend(file_data.nodes)
                all_edges.extend(file_data.edges)

        store.replace_segment(segment_ref.id, all_nodes, all_edges, indexed_at=indexed_at)
        return GraphIndexSummary(
            segment_id=segment_ref.id,
            db_path=str(store.db_path),
            node_count=len(all_nodes),
            edge_count=len(all_edges),
            indexed_at=indexed_at,
        )

    def _index_file(
        self,
        segment_id: str,
        segment_root: Path,
        file_path: Path,
        builder: SkeletonMapBuilder,
    ) -> _FileGraphData:
        parse_result = builder.build(file_path)
        file_rel = str(file_path.relative_to(segment_root))
        nodes = [
            GraphNode(
                id=make_node_id(segment_id, file_rel, symbol.qualified_name),
                segment_id=segment_id,
                file_rel=file_rel,
                symbol_name=symbol.name,
                qualified_name=symbol.qualified_name,
                kind=symbol.kind,
                line=symbol.start_line,
                metadata_json=None,
            )
            for symbol in parse_result.symbols
        ]

        edges = self._extract_edges(segment_id, file_path, nodes)
        return _FileGraphData(nodes=nodes, edges=edges)

    def _extract_edges(
        self,
        segment_id: str,
        file_path: Path,
        nodes: list[GraphNode],
    ) -> list[GraphEdge]:
        content = file_path.read_text(errors="replace")
        try:
            tree = ast_module.parse(content, filename=str(file_path))
        except SyntaxError:
            return []

        caller_ids = {node.symbol_name: node.id for node in nodes if node.kind == "function"}
        call_target_ids = {
            node.symbol_name: node.id for node in nodes if node.kind in {"function", "class"}
        }
        edges: list[GraphEdge] = []

        for node in tree.body:
            if not isinstance(node, (ast_module.FunctionDef, ast_module.AsyncFunctionDef)):
                continue
            caller_id = caller_ids.get(node.name)
            if caller_id is None:
                continue
            collector = _DirectCallCollector()
            for statement in node.body:
                collector.visit(statement)
            for callee_name in collector.call_names:
                callee_id = call_target_ids.get(callee_name)
                if callee_id is None or callee_id == caller_id:
                    continue
                edge_id = make_edge_id(segment_id, caller_id, callee_id, "calls")
                edges.append(
                    GraphEdge(
                        id=edge_id,
                        segment_id=segment_id,
                        from_node_id=caller_id,
                        to_node_id=callee_id,
                        edge_kind="calls",
                        source="ast",
                        confidence=1.0,
                    )
                )

        deduped: dict[str, GraphEdge] = {edge.id: edge for edge in edges}
        return list(deduped.values())
