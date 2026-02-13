import typer  # type: ignore
import time
import json
from pathlib import Path
from typing import Optional
from src.infrastructure.telemetry import Telemetry
from src.domain.result import Ok, Err
from src.application.symbol_selector import SymbolQuery
from src.application.ast_parser import SkeletonMapBuilder, ParseResult
from src.domain.ast_cache import SQLiteCache
from src.infrastructure.factories import get_ast_cache, get_ast_cache_db_path

ast_app = typer.Typer(help="AST & Parsing Commands")


def _json_output(data: dict):
    typer.echo(json.dumps(data, indent=2))


def _get_telemetry(level: str = "lite") -> Optional[Telemetry]:
    if level == "off":
        return None
    return Telemetry(Path.cwd(), level=level)


CACHE_DIR_NAME = ".trifecta"


# removed local _get_cache in favor of factory


@ast_app.command("symbols")
def symbols(
    uri: str = typer.Argument(..., help="sym://python/mod|type/..."),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("off", "--telemetry"),
    persist_cache: bool = typer.Option(
        False, "--persist-cache", help="Use persistent SQLite cache"
    ),
):
    """Return symbols from Python modules using AST parsing (M1)."""
    root = Path(segment).resolve()
    telemetry = _get_telemetry(telemetry_level)
    cache = get_ast_cache(persist=persist_cache, segment_id=str(root), telemetry=telemetry)
    cache_db_path = get_ast_cache_db_path(str(root)) if persist_cache else None

    try:
        # 1. Parse URI
        match SymbolQuery.parse(uri):
            case Err(e):
                _json_output({"status": "error", "error_code": e.code, "message": e.message})
                raise typer.Exit(1)
            case Ok(q):
                query = q
            case _:
                _json_output(
                    {
                        "status": "error",
                        "error_code": "PARSE_ERROR",
                        "message": "Failed to parse URI",
                    }
                )
                raise typer.Exit(1)

        # 2. Resolve file_path (lean, fail-closed)
        path_as_dir = query.path.replace(".", "/")
        candidate_file = root / f"{path_as_dir}.py"
        candidate_init = root / path_as_dir / "__init__.py"

        if candidate_file.exists() and candidate_file.is_file():
            file_path = candidate_file
        elif candidate_init.exists() and candidate_init.is_file():
            file_path = candidate_init
        else:
            _json_output(
                {
                    "status": "error",
                    "error_code": "FILE_NOT_FOUND",
                    "message": f"Could not find module for {query.path}",
                }
            )
            raise typer.Exit(1)

        # 3. Invoke SkeletonMapBuilder with cache (M1 REAL)
        miss_reason = None
        if persist_cache and cache_db_path is not None:
            if not cache_db_path.exists():
                miss_reason = "cold_cache_db_missing"
            else:
                stats_snapshot = SQLiteCache(db_path=cache_db_path).stats()
                miss_reason = "cold_cache_empty" if stats_snapshot.entries == 0 else "key_miss"
        elif not persist_cache:
            miss_reason = "ephemeral_cache"

        t0 = time.perf_counter_ns()
        builder = SkeletonMapBuilder(cache=cache, segment_id=str(root))
        result: ParseResult = builder.build(file_path)
        duration_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        if result.status == "hit":
            miss_reason = "cache_hit"

        # 4. Return JSON (M1 Contract) with cache info
        output = {
            "status": "ok",
            "segment_root": str(root),
            "file_rel": str(file_path.relative_to(root)),
            "symbols": [
                {"kind": s.kind, "name": s.name, "line": s.start_line} for s in result.symbols
            ],
            "cache_status": result.status,
            "cache_key": result.cache_key,
            "miss_reason": miss_reason,
            "cache_db_path": str(cache_db_path) if cache_db_path else None,
        }

        if telemetry:
            telemetry.event(
                "ast.symbols",
                {},
                {"status": "ok"},
                duration_ms,
                file=str(file_path.relative_to(root)),
                symbols_count=len(result.symbols),
                cache_status=result.status,
                cache_key=result.cache_key,
                miss_reason=miss_reason,
                cache_db_path=str(cache_db_path) if cache_db_path else "",
            )
            telemetry.flush()

        _json_output(output)

    except typer.Exit:
        raise
    except Exception as e:
        _json_output({"status": "error", "error_code": "INTERNAL_ERROR", "message": str(e)})
        raise typer.Exit(1)


@ast_app.command("snippet")
def snippet(uri: str = typer.Argument(...)):
    telemetry = _get_telemetry("lite")
    if telemetry:
        telemetry.event(
            "ast.snippet.not_implemented",
            {"uri": uri},
            {"status": "error", "error_code": "NOT_IMPLEMENTED"},
            1,
        )
        telemetry.flush()
    _json_output(
        {
            "status": "error",
            "error_code": "NOT_IMPLEMENTED",
            "message": "ast snippet is not implemented yet; use ast symbols for deterministic output.",
            "hint": "Use `trifecta ast symbols <uri>` for deterministic symbol extraction.",
            "context": {
                "command": "ast.snippet",
                "uri": uri,
            },
        }
    )
    raise typer.Exit(1)


@ast_app.command("hover")
def hover(
    uri: str = typer.Argument(..., help="File path to hover over"),
    line: int = typer.Option(..., "--line", "-l"),
    character: int = typer.Option(..., "--char", "-c"),
    segment: str = typer.Option(".", "--segment"),
):
    """[WIP] LSP Hover request."""
    telemetry = _get_telemetry("lite")
    if telemetry:
        telemetry.event(
            "ast.hover.wip",
            {"segment": segment, "uri": uri, "line": line, "char": character},
            {"status": "ok", "backend": "wip_stub"},
            1,
        )
        telemetry.flush()

    # Stub for now
    _json_output(
        {
            "status": "ok",
            "kind": "skeleton",
            "backend": "wip_stub",
            "capability_state": "WIP",
            "response_state": "partial",
            "data": {"uri": uri, "range": {"start_line": 1, "end_line": 10}, "children": []},
        }
    )


@ast_app.command("clear-cache")
def clear_cache(
    segment: str = typer.Option(".", "--segment"),
):
    """Clear AST cache for the segment."""
    root = Path(segment).resolve()
    cache_path = get_ast_cache_db_path(str(root))

    if cache_path.exists():
        cache_path.unlink()
        _json_output(
            {
                "status": "ok",
                "message": f"Cache cleared for segment: {segment}",
                "cache_path": str(cache_path),
            }
        )
    else:
        _json_output(
            {
                "status": "ok",
                "message": f"No cache found for segment: {segment}",
                "cache_path": str(cache_path),
            }
        )


@ast_app.command("cache-stats")
def cache_stats(
    segment: str = typer.Option(".", "--segment"),
):
    """Show AST cache statistics for the segment."""
    root = Path(segment).resolve()
    db_path = get_ast_cache_db_path(str(root))

    if db_path.exists():
        cache = SQLiteCache(db_path=db_path)
        stats = cache.stats()
        _json_output(
            {
                "status": "ok",
                "segment": segment,
                "cache_path": str(db_path),
                "stats": {
                    "entries": stats.entries,
                    "bytes": stats.current_bytes,
                    "hits": stats.hits,
                    "misses": stats.misses,
                    "hit_rate": f"{stats.hit_rate:.2%}"
                    if stats.hits + stats.misses > 0
                    else "0.00%",
                },
            }
        )
    else:
        _json_output(
            {
                "status": "ok",
                "segment": segment,
                "cache_path": str(db_path),
                "message": "No cache found (cache not initialized)",
            }
        )
