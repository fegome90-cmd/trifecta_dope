import json
from pathlib import Path
from typing import Any

import typer

from src.application.graph_indexer import GraphIndexer
from src.application.graph_service import GraphService
from src.infrastructure.graph_store import GraphTargetResolutionError


graph_app = typer.Typer(help="Code Graph Commands")


def _emit(data: dict[str, object], json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(data, indent=2))
        return

    if data.get("status") != "ok":
        typer.echo(str(data))
        return

    if "node_count" in data and "edge_count" in data:
        typer.echo(
            f"segment={data['segment_id']} nodes={data['node_count']} edges={data['edge_count']}"
        )
        return

    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        nodes = []
    typer.echo(f"{len(nodes)} result(s)")
    for node in nodes:
        typer.echo(f"- {node['symbol_name']} [{node['kind']}] {node['file_rel']}:{node['line']}")


def _handle_target_resolution_error(exc: GraphTargetResolutionError, json_output: bool) -> None:
    """Handle graph target resolution errors with structured JSON output."""
    payload: dict[str, Any] = {
        "status": "error",
        "segment_id": exc.segment_id,
        "symbol": exc.symbol,
        "error": exc.to_error_payload(),
    }
    _emit(payload, json_output)
    raise typer.Exit(code=1)


@graph_app.command("index")
def index(
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    summary = GraphIndexer().index_segment(Path(segment))
    _emit({"status": "ok", **summary.to_dict()}, json_output)


@graph_app.command("status")
def status(
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    _emit(GraphService().status(Path(segment)), json_output)


@graph_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q"),
    segment: str = typer.Option(".", "--segment", "-s"),
    limit: int = typer.Option(20, "--limit"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    _emit(GraphService().search(Path(segment), query, limit=limit), json_output)


@graph_app.command("callers")
def callers(
    symbol: str = typer.Option(..., "--symbol"),
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        _emit(GraphService().callers(Path(segment), symbol), json_output)
    except GraphTargetResolutionError as exc:
        _handle_target_resolution_error(exc, json_output)


@graph_app.command("callees")
def callees(
    symbol: str = typer.Option(..., "--symbol"),
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        _emit(GraphService().callees(Path(segment), symbol), json_output)
    except GraphTargetResolutionError as exc:
        _handle_target_resolution_error(exc, json_output)
