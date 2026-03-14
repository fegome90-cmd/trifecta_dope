import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.domain.graph_models import GraphEdge, GraphNode, GraphStatus


class GraphCommandError(ValueError):
    # Stable Graph CLI envelope: code/kind/message/details are always present.
    # Specialized families may add fields such as candidates.
    code = "GRAPH_COMMAND_ERROR"
    kind = "graph_command_error"

    def __init__(
        self,
        segment_id: str,
        message: str,
        symbol: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self.segment_id = segment_id
        self.symbol = symbol
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_error_payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "kind": self.kind,
            "message": self.message,
            "details": self.details,
        }


class GraphTargetResolutionError(GraphCommandError):
    code = "GRAPH_TARGET_RESOLUTION_ERROR"
    kind = "graph_target_resolution_error"

    def __init__(
        self,
        segment_id: str,
        symbol: str,
        message: str,
        candidates: list[GraphNode] | None = None,
    ) -> None:
        self.candidates = [candidate.to_dict() for candidate in (candidates or [])]
        super().__init__(segment_id=segment_id, symbol=symbol, message=message, details={})

    def to_error_payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "kind": self.kind,
            "message": self.message,
            "details": self.details,
            "candidates": self.candidates,
        }


class AmbiguousGraphTargetError(GraphTargetResolutionError):
    code = "GRAPH_TARGET_AMBIGUOUS"
    kind = "ambiguous_symbol"

    def __init__(self, segment_id: str, symbol: str, candidates: list[GraphNode]) -> None:
        super().__init__(
            segment_id=segment_id,
            symbol=symbol,
            message=f"Symbol '{symbol}' matched multiple graph nodes.",
            candidates=candidates,
        )


class GraphTargetNotFoundError(GraphTargetResolutionError):
    code = "GRAPH_TARGET_NOT_FOUND"
    kind = "symbol_not_found"

    def __init__(self, segment_id: str, symbol: str) -> None:
        super().__init__(
            segment_id=segment_id,
            symbol=symbol,
            message=f"Symbol '{symbol}' was not found in the graph index.",
            candidates=[],
        )


class GraphStoreAccessError(GraphCommandError):
    code = "GRAPH_DB_UNAVAILABLE"
    kind = "graph_db_unavailable"

    def __init__(
        self,
        segment_id: str,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(segment_id=segment_id, message=message, details=details)


class GraphStoreSchemaMismatchError(GraphStoreAccessError):
    code = "GRAPH_DB_SCHEMA_MISMATCH"
    kind = "graph_db_schema_mismatch"

    def __init__(self, segment_id: str, expected_version: int, actual_version: int | str) -> None:
        super().__init__(
            segment_id=segment_id,
            message=(
                f"Graph DB schema version mismatch: expected {expected_version}, "
                f"got {actual_version}."
            ),
            details={
                "expected_version": expected_version,
                "actual_version": actual_version,
            },
        )


class GraphStoreIncompleteError(GraphStoreAccessError):
    code = "GRAPH_DB_INCOMPLETE"
    kind = "graph_db_incomplete"

    def __init__(self, segment_id: str, missing_tables: list[str]) -> None:
        sorted_missing = sorted(missing_tables)
        super().__init__(
            segment_id=segment_id,
            message=(
                "Graph DB is missing required tables: "
                + ", ".join(sorted_missing)
                + "."
            ),
            details={"missing_tables": sorted_missing},
        )


class GraphStoreUnavailableError(GraphStoreAccessError):
    code = "GRAPH_DB_UNAVAILABLE"
    kind = "graph_db_unavailable"

    def __init__(self, segment_id: str, cause: str) -> None:
        super().__init__(
            segment_id=segment_id,
            message=f"Graph DB could not be opened or queried: {cause}",
        )


class GraphStore:
    SCHEMA_VERSION = 1
    REQUIRED_TABLES = ("graph_index", "nodes", "edges")

    def __init__(
        self,
        db_path: Path,
        initialize: bool = True,
        segment_id: str = "graph_index",
    ) -> None:
        self._db_path = db_path
        self._segment_id = segment_id
        if initialize:
            self._validate_or_init_writable_schema(segment_id=self._segment_id)
            self._init_db()

    @property
    def db_path(self) -> Path:
        return self._db_path

    @staticmethod
    def db_path_for_segment(segment_root: Path, segment_id: str) -> Path:
        return segment_root / ".trifecta" / "cache" / f"graph_{segment_id}.db"

    @classmethod
    def open_readonly(cls, db_path: Path, segment_id: str) -> "GraphStore":
        store = cls.__new__(cls)
        store._db_path = db_path
        store._segment_id = segment_id
        store._validate_existing_schema(segment_id)
        return store

    @classmethod
    def probe_status(cls, db_path: Path, segment_id: str) -> GraphStatus:
        if not db_path.exists():
            return GraphStatus(
                exists=False,
                segment_id=segment_id,
                db_path=str(db_path),
                node_count=0,
                edge_count=0,
                last_indexed_at=None,
            )
        return cls.open_readonly(db_path, segment_id).get_status(segment_id)

    def _validate_or_init_writable_schema(self, segment_id: str) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._db_path.exists():
            try:
                conn = sqlite3.connect(self._db_path)
                conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
                conn.execute("INSERT INTO schema_version VALUES (?)", (self.SCHEMA_VERSION,))
                conn.commit()
                conn.close()
            except sqlite3.Error as exc:
                raise GraphStoreUnavailableError(segment_id, str(exc)) from exc
            return

        # Writable repair is intentionally conservative: only a DB that already
        # advertises the current graph schema_version is recoverable in place.
        self._validate_schema_version(segment_id)

    def _validate_existing_schema(self, segment_id: str) -> None:
        conn = self._connect(segment_id)
        try:
            tables = self._list_tables(conn, segment_id)
            self._validate_schema_version_from_tables(conn, segment_id, tables)

            missing_tables = [table for table in self.REQUIRED_TABLES if table not in tables]
            if missing_tables:
                raise GraphStoreIncompleteError(segment_id, missing_tables)
        finally:
            conn.close()

    def _validate_schema_version(self, segment_id: str) -> None:
        conn = self._connect(segment_id)
        try:
            tables = self._list_tables(conn, segment_id)
            self._validate_schema_version_from_tables(conn, segment_id, tables)
        finally:
            conn.close()

    def _validate_schema_version_from_tables(
        self,
        conn: sqlite3.Connection,
        segment_id: str,
        tables: set[str],
    ) -> None:
        if "schema_version" not in tables:
            raise GraphStoreIncompleteError(segment_id, ["schema_version"])

        row = conn.execute("SELECT version FROM schema_version").fetchone()
        actual_version: int | str = row[0] if row is not None else "none"
        if actual_version != self.SCHEMA_VERSION:
            raise GraphStoreSchemaMismatchError(segment_id, self.SCHEMA_VERSION, actual_version)

    def _connect(self, segment_id: str) -> sqlite3.Connection:
        try:
            return sqlite3.connect(self._db_path)
        except sqlite3.Error as exc:
            raise GraphStoreUnavailableError(segment_id, str(exc)) from exc

    def _list_tables(self, conn: sqlite3.Connection, segment_id: str) -> set[str]:
        try:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        except sqlite3.Error as exc:
            raise GraphStoreUnavailableError(segment_id, str(exc)) from exc
        return {str(row[0]) for row in rows}

    def _init_db(self) -> None:
        conn = self._connect(self._segment_id)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS graph_index ("
                "segment_id TEXT PRIMARY KEY, "
                "indexed_at TEXT NOT NULL"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS nodes ("
                "id TEXT PRIMARY KEY, "
                "segment_id TEXT NOT NULL, "
                "file_rel TEXT NOT NULL, "
                "symbol_name TEXT NOT NULL, "
                "qualified_name TEXT NOT NULL, "
                "kind TEXT NOT NULL, "
                "line INTEGER NOT NULL, "
                "metadata_json TEXT"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS edges ("
                "id TEXT PRIMARY KEY, "
                "segment_id TEXT NOT NULL, "
                "from_node_id TEXT NOT NULL, "
                "to_node_id TEXT NOT NULL, "
                "edge_kind TEXT NOT NULL, "
                "source TEXT NOT NULL, "
                "confidence REAL"
                ")"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_nodes_segment_search "
                "ON nodes(segment_id, symbol_name, qualified_name, file_rel)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_edges_segment_from "
                "ON edges(segment_id, from_node_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_edges_segment_to "
                "ON edges(segment_id, to_node_id)"
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise GraphStoreUnavailableError(self._segment_id, str(exc)) from exc
        finally:
            conn.close()

    def replace_segment(
        self,
        segment_id: str,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        indexed_at: str | None = None,
    ) -> None:
        timestamp = indexed_at or datetime.now(timezone.utc).isoformat()
        conn = self._connect(segment_id)
        try:
            conn.execute("DELETE FROM edges WHERE segment_id = ?", (segment_id,))
            conn.execute("DELETE FROM nodes WHERE segment_id = ?", (segment_id,))
            conn.execute(
                "INSERT OR REPLACE INTO graph_index(segment_id, indexed_at) VALUES (?, ?)",
                (segment_id, timestamp),
            )
            conn.executemany(
                "INSERT OR REPLACE INTO nodes("
                "id, segment_id, file_rel, symbol_name, qualified_name, kind, line, metadata_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        node.id,
                        node.segment_id,
                        node.file_rel,
                        node.symbol_name,
                        node.qualified_name,
                        node.kind,
                        node.line,
                        node.metadata_json,
                    )
                    for node in nodes
                ],
            )
            conn.executemany(
                "INSERT OR REPLACE INTO edges("
                "id, segment_id, from_node_id, to_node_id, edge_kind, source, confidence"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        edge.id,
                        edge.segment_id,
                        edge.from_node_id,
                        edge.to_node_id,
                        edge.edge_kind,
                        edge.source,
                        edge.confidence,
                    )
                    for edge in edges
                ],
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise GraphStoreUnavailableError(segment_id, str(exc)) from exc
        finally:
            conn.close()

    def get_status(self, segment_id: str) -> GraphStatus:
        conn = sqlite3.connect(self._db_path)
        node_count = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE segment_id = ?",
            (segment_id,),
        ).fetchone()[0]
        edge_count = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE segment_id = ?",
            (segment_id,),
        ).fetchone()[0]
        indexed_row = conn.execute(
            "SELECT indexed_at FROM graph_index WHERE segment_id = ?",
            (segment_id,),
        ).fetchone()
        conn.close()
        return GraphStatus(
            exists=self._db_path.exists(),
            segment_id=segment_id,
            db_path=str(self._db_path),
            node_count=node_count,
            edge_count=edge_count,
            last_indexed_at=indexed_row[0] if indexed_row else None,
        )

    def search_nodes(self, segment_id: str, query: str, limit: int = 20) -> list[GraphNode]:
        pattern = f"%{query.lower()}%"
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM nodes "
            "WHERE segment_id = ? AND ("
            "lower(symbol_name) LIKE ? OR lower(qualified_name) LIKE ? OR lower(file_rel) LIKE ?"
            ") "
            "ORDER BY CASE WHEN lower(symbol_name) = ? THEN 0 ELSE 1 END, file_rel, line "
            "LIMIT ?",
            (segment_id, pattern, pattern, pattern, query.lower(), limit),
        ).fetchall()
        conn.close()
        return [self._row_to_node(row) for row in rows]

    def get_callers(self, segment_id: str, symbol: str) -> list[GraphNode]:
        target_node = self._resolve_target_node(segment_id, symbol)
        return self.get_callers_for_node(segment_id, target_node.id)

    def get_callees(self, segment_id: str, symbol: str) -> list[GraphNode]:
        target_node = self._resolve_target_node(segment_id, symbol)
        return self.get_callees_for_node(segment_id, target_node.id)

    def get_callers_for_node(self, segment_id: str, node_id: str) -> list[GraphNode]:
        return self._get_related_nodes_for_node(segment_id, node_id, reverse=True)

    def get_callees_for_node(self, segment_id: str, node_id: str) -> list[GraphNode]:
        return self._get_related_nodes_for_node(segment_id, node_id, reverse=False)

    def find_target_candidates(self, segment_id: str, symbol: str) -> list[GraphNode]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM nodes "
            "WHERE segment_id = ? AND (symbol_name = ? OR qualified_name = ?) "
            "ORDER BY file_rel, line",
            (segment_id, symbol, symbol),
        ).fetchall()
        conn.close()
        return [self._row_to_node(row) for row in rows]

    def _resolve_target_node(self, segment_id: str, symbol: str) -> GraphNode:
        target_candidates = self.find_target_candidates(segment_id, symbol)
        if not target_candidates:
            raise GraphTargetNotFoundError(segment_id, symbol)
        if len(target_candidates) > 1:
            raise AmbiguousGraphTargetError(segment_id, symbol, target_candidates)
        return target_candidates[0]

    def _get_related_nodes_for_node(
        self, segment_id: str, node_id: str, reverse: bool
    ) -> list[GraphNode]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT n.* FROM nodes n "
            "JOIN edges e ON "
            + ("e.from_node_id = n.id " if reverse else "e.to_node_id = n.id ")
            + "JOIN nodes target ON "
            + ("e.to_node_id = target.id " if reverse else "e.from_node_id = target.id ")
            + "WHERE target.segment_id = ? AND target.id = ? "
            "ORDER BY n.file_rel, n.line",
            (segment_id, node_id),
        ).fetchall()
        conn.close()
        return [self._row_to_node(row) for row in rows]

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> GraphNode:
        return GraphNode(
            id=row["id"],
            segment_id=row["segment_id"],
            file_rel=row["file_rel"],
            symbol_name=row["symbol_name"],
            qualified_name=row["qualified_name"],
            kind=row["kind"],
            line=row["line"],
            metadata_json=row["metadata_json"],
        )
