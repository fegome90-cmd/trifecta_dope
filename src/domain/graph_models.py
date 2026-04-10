from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class GraphNode:
    id: str
    segment_id: str
    file_rel: str
    symbol_name: str
    qualified_name: str
    kind: str
    line: int
    metadata_json: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GraphEdge:
    id: str
    segment_id: str
    from_node_id: str
    to_node_id: str
    edge_kind: str
    source: str = "ast"
    confidence: Optional[float] = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GraphIndexSummary:
    segment_id: str
    db_path: str
    node_count: int
    edge_count: int
    indexed_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GraphStatus:
    exists: bool
    segment_id: str
    db_path: str
    node_count: int
    edge_count: int
    last_indexed_at: Optional[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def make_node_id(segment_id: str, file_rel: str, qualified_name: str) -> str:
    return f"{segment_id}:{file_rel}:{qualified_name}"


def make_edge_id(segment_id: str, from_node_id: str, to_node_id: str, edge_kind: str) -> str:
    return f"{segment_id}:{from_node_id}->{to_node_id}:{edge_kind}"
