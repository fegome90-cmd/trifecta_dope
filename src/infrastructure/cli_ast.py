import typer
import time
import json
from pathlib import Path
from typing import Optional
from src.infrastructure.telemetry import Telemetry
from src.domain.result import Ok, Err
from src.application.symbol_selector import SymbolQuery
from src.application.ast_parser import SkeletonMapBuilder

ast_app = typer.Typer(help="AST & Parsing Commands")


def _json_output(data: dict):
    print(json.dumps(data, indent=2))


def _get_telemetry(level: str = "lite") -> Optional[Telemetry]:
    if level == "off":
        return None
    return Telemetry(Path.cwd(), level=level)


@ast_app.command("symbols")
def symbols(
    uri: str = typer.Argument(..., help="sym://python/mod|type/..."),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("off", "--telemetry"),
):
    """Return symbols from Python modules using AST parsing (M1)."""
    root = Path(segment).resolve()
    telemetry = _get_telemetry(telemetry_level)

    try:
        # 1. Parse URI
        match SymbolQuery.parse(uri):
            case Err(e):
                _json_output({"status": "error", "error_code": e.code, "message": e.message})
                raise typer.Exit(1)
            case Ok(query):
                pass

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

        # 3. Invoke SkeletonMapBuilder (M1 REAL)
        t0 = time.perf_counter_ns()
        builder = SkeletonMapBuilder()
        symbols = builder.build(file_path)
        duration_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        # 4. Return JSON (M1 Contract)
        output = {
            "status": "ok",
            "segment_root": str(root),
            "file_rel": str(file_path.relative_to(root)),
            "symbols": [{"kind": s.kind, "name": s.name, "line": s.start_line} for s in symbols],
        }

        if telemetry:
            telemetry.event(
                "ast.symbols",
                {},
                {"status": "ok"},
                duration_ms,
                file=str(file_path.relative_to(root)),
                symbols_count=len(symbols),
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
    pass  # Minimal stub


@ast_app.command("hover")
def hover(
    uri: str = typer.Argument(..., help="File path to hover over"),
    line: int = typer.Option(..., "--line", "-l"),
    character: int = typer.Option(..., "--char", "-c"),
    segment: str = typer.Option(".", "--segment"),
):
    """[WIP] LSP Hover request."""
    # Stub for now
    _json_output(
        {
            "status": "ok",
            "kind": "skeleton",
            "data": {"uri": uri, "range": {"start_line": 1, "end_line": 10}, "children": []},
        }
    )
