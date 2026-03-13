from pathlib import Path

from src.domain.segment_resolver import resolve_segment_ref
from src.infrastructure.graph_store import GraphStore


class GraphService:
    def __init__(self, store: GraphStore | None = None) -> None:
        self._store = store

    def status(self, segment: Path | str) -> dict[str, object]:
        segment_ref, store = self._resolve(segment)
        status = store.get_status(segment_ref.id)
        return {"status": "ok", **status.to_dict()}

    def search(self, segment: Path | str, query: str, limit: int = 20) -> dict[str, object]:
        segment_ref, store = self._resolve(segment)
        nodes = store.search_nodes(segment_ref.id, query, limit=limit)
        return {
            "status": "ok",
            "segment_id": segment_ref.id,
            "query": query,
            "nodes": [node.to_dict() for node in nodes],
        }

    def callers(self, segment: Path | str, symbol: str) -> dict[str, object]:
        return self._related(segment, symbol, reverse=True)

    def callees(self, segment: Path | str, symbol: str) -> dict[str, object]:
        return self._related(segment, symbol, reverse=False)

    def related_terms(self, segment: Path | str, query: str) -> dict[str, object]:
        segment_ref, store = self._resolve(segment)
        nodes = store.search_nodes(segment_ref.id, query, limit=1)
        if not nodes:
            return {"status": "ok", "segment_id": segment_ref.id, "terms": []}
        first = nodes[0]
        return {
            "status": "ok",
            "segment_id": segment_ref.id,
            "terms": [first.symbol_name, first.file_rel],
        }

    def _related(self, segment: Path | str, symbol: str, reverse: bool) -> dict[str, object]:
        segment_ref, store = self._resolve(segment)
        nodes = (
            store.get_callers(segment_ref.id, symbol)
            if reverse
            else store.get_callees(segment_ref.id, symbol)
        )
        return {
            "status": "ok",
            "segment_id": segment_ref.id,
            "symbol": symbol,
            "nodes": [node.to_dict() for node in nodes],
        }

    def _resolve(self, segment: Path | str) -> tuple[object, GraphStore]:
        segment_ref = resolve_segment_ref(segment)
        store = self._store or GraphStore(
            GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)
        )
        return segment_ref, store
