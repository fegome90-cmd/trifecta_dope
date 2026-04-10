# Trifecta Graph MVP Contract

## Scope

The Trifecta Graph MVP is a local code-navigation signal built with:

- AST-only indexing
- SQLite-only storage
- SegmentRef V1 as the operational segment binding

It exposes these CLI commands under `trifecta graph`:

- `graph index`
- `graph status`
- `graph search`
- `graph callers`
- `graph callees`

## Boundaries

- Python source only via AST
- Top-level symbols only
- Top-level direct `ast.Name` calls only
- No LSP in the critical path
- No symbol-to-chunk linking
- No prompt or context builders
- No MCP integration
- No V2 segment binding

Graph is a navigation and signal surface. It is not a textual retrieval layer.

## Segment Binding

Graph commands bind segment identity through `resolve_segment_ref()` from SegmentRef V1.

Operational consequences:

- `segment_ref.root_abs` is the canonical segment root
- `segment_ref.id` is the graph segment identity used in storage and responses
- graph DB paths derive from SegmentRef V1, not ad hoc path hashing

## Storage Model

The graph DB lives under:

```text
.trifecta/cache/graph_<segment_id>.db
```

Read paths are non-mutating on pristine segments and fail closed on invalid existing DBs.

## Recoverable vs Invalid DB

### Recoverable partial DB

An existing DB is recoverable only when:

- it is a SQLite DB
- it contains `schema_version`
- `schema_version == 1`

For `graph index`, that is enough to repair the DB in place.

For read-only commands, "recoverable" is command-specific and means the DB has the
minimum tables required to answer without inventing data:

- `graph status`: `graph_index`, `nodes`, `edges`
- `graph search`: `nodes`
- `graph callers`: `nodes`, `edges`
- `graph callees`: `nodes`, `edges`

### Invalid or non-recoverable DB

A DB is invalid or non-recoverable when:

- `schema_version` is missing
- `schema_version` does not match the expected version
- the DB path cannot be opened or queried
- a read-only command lacks the minimum required tables for that command

In those cases Graph fails closed. It does not repair on read paths, and `graph index` does not silently recover a DB that does not already advertise the current graph schema.

## Exit Codes

- `0`: successful command execution
- `1`: predictable Graph failure

The Graph CLI does not currently expose a richer exit-code matrix than `0/1`.

## Error Envelope

All predictable Graph CLI failures use this envelope:

```json
{
  "ok": false,
  "segment_id": "...",
  "symbol": "...",
  "error": {
    "code": "...",
    "message": "...",
    "retryable": false,
    "details": {}
  }
}
```

Rules:

- `ok`, `segment_id`, and `error` are always present
- `symbol` appears for symbol-scoped commands when relevant
- `error.code`, `error.message`, `error.retryable`, and `error.details` are the stable base
- specialized machine-readable data such as ambiguous candidates lives under `error.details`

## Frozen Error Codes

Resolution:

- `GRAPH_TARGET_NOT_FOUND`
- `GRAPH_TARGET_AMBIGUOUS`

Store and DB access:

- `GRAPH_DB_UNAVAILABLE`
- `GRAPH_DB_INCOMPLETE`
- `GRAPH_DB_SCHEMA_MISMATCH`

## Query Semantics

- `search` is fuzzy and returns matching nodes
- `callers` and `callees` use exact target resolution and fail closed on ambiguity

## Non-Goals

This MVP does not provide:

- inter-file semantic resolution beyond the current AST-only rules
- textual retrieval or passage ranking
- LSP-backed enrichment
- graph ranking
- language-server dependency for correctness
