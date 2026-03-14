from pathlib import Path

from src.domain.segment_resolver import SegmentRef, resolve_segment_ref
from src.infrastructure.graph_store import (
    AmbiguousGraphTargetError,
    GraphStore,
    GraphTargetNotFoundError,
)


class GraphService:
    def __init__(self, store: GraphStore | None = None) -> None:
        self._store = store

    def status(self, segment: Path | str) -> dict[str, object]:
        segment_ref = resolve_segment_ref(segment)
        if self._store is not None:
            status = self._store.get_status(segment_ref.id)
        else:
            db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)
            status = GraphStore.probe_status(db_path, segment_ref.id)
        return {"status": "ok", **status.to_dict()}

    def search(self, segment: Path | str, query: str, limit: int = 20) -> dict[str, object]:
        # Search stays fuzzy on purpose; exact symbol resolution is only for callers/callees.
        resolved = self._resolve_existing(segment)
        if resolved is None:
            segment_ref = resolve_segment_ref(segment)
            return {"status": "ok", "segment_id": segment_ref.id, "query": query, "nodes": []}
        segment_ref, store = resolved
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
        resolved = self._resolve_existing(segment)
        if resolved is None:
            segment_ref = resolve_segment_ref(segment)
            return {"status": "ok", "segment_id": segment_ref.id, "terms": []}
        segment_ref, store = resolved
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
        resolved = self._resolve_existing(segment)
        if resolved is None:
            segment_ref = resolve_segment_ref(segment)
            return {
                "status": "ok",
                "segment_id": segment_ref.id,
                "symbol": symbol,
                "nodes": [],
            }
        segment_ref, store = resolved
        target_node = self._resolve_related_target(store, segment_ref.id, symbol)
        nodes = (
            store.get_callers_for_node(segment_ref.id, target_node.id)
            if reverse
            else store.get_callees_for_node(segment_ref.id, target_node.id)
        )
        return {
            "status": "ok",
            "segment_id": segment_ref.id,
            "symbol": symbol,
            "nodes": [node.to_dict() for node in nodes],
        }

    def _resolve_related_target(self, store: GraphStore, segment_id: str, symbol: str):
        matches = store.find_target_candidates(segment_id, symbol)
        if not matches:
            raise GraphTargetNotFoundError(segment_id, symbol)
        if len(matches) > 1:
            raise AmbiguousGraphTargetError(segment_id, symbol, matches)
        return matches[0]

    def _resolve_existing(self, segment: Path | str) -> tuple[SegmentRef, GraphStore] | None:
        segment_ref = resolve_segment_ref(segment)
        db_path = GraphStore.db_path_for_segment(segment_ref.root_abs, segment_ref.id)
        if self._store is not None:
            return segment_ref, self._store
        if not db_path.exists():
            return None
        return segment_ref, GraphStore(db_path)
