import json
from pathlib import Path
from typing import Any

import typer

from src.application.graph_indexer import GraphIndexer
from src.application.graph_service import GraphService
from src.infrastructure.graph_store import GraphCommandError


graph_app = typer.Typer(help="Code Graph Commands")


def _emit(data: dict[str, object], json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(data, indent=2))
        return

    if data.get("ok") is False:
        error = data.get("error")
        if isinstance(error, dict):
            typer.echo(f"{error.get('code')}: {error.get('message')}", err=True)
        else:
            typer.echo(str(data), err=True)
        return

    if "node_count" in data and "edge_count" in data:
        typer.echo(
            f"segment={data.get('segment_id', '?')} nodes={data.get('node_count', 0)} edges={data.get('edge_count', 0)}"
        )
        return

    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        nodes = []
    typer.echo(f"{len(nodes)} result(s)")
    for node in nodes:
        typer.echo(
            f"- {node.get('symbol_name', '?')} [{node.get('kind', '?')}]"
            f" {node.get('file_rel', '?')}:{node.get('line', '?')}"
        )


def _handle_graph_error(exc: GraphCommandError, json_output: bool) -> None:
    payload: dict[str, Any] = {
        "ok": False,
        "segment_id": exc.segment_id,
        "error": exc.to_error_payload(),
    }
    if exc.symbol is not None:
        payload["symbol"] = exc.symbol
    _emit(payload, json_output)
    raise typer.Exit(code=exc.exit_code)


@graph_app.command("index")
def index(
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        summary = GraphIndexer().index_segment(Path(segment))
        _emit({"status": "ok", **summary.to_dict()}, json_output)
    except GraphCommandError as exc:
        _handle_graph_error(exc, json_output)


@graph_app.command("status")
def status(
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        _emit(GraphService().status(Path(segment)), json_output)
    except GraphCommandError as exc:
        _handle_graph_error(exc, json_output)


@graph_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q"),
    segment: str = typer.Option(".", "--segment", "-s"),
    limit: int = typer.Option(20, "--limit"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        _emit(GraphService().search(Path(segment), query, limit=limit), json_output)
    except GraphCommandError as exc:
        _handle_graph_error(exc, json_output)


@graph_app.command("callers")
def callers(
    symbol: str = typer.Option(..., "--symbol"),
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        _emit(GraphService().callers(Path(segment), symbol), json_output)
    except GraphCommandError as exc:
        _handle_graph_error(exc, json_output)


@graph_app.command("callees")
def callees(
    symbol: str = typer.Option(..., "--symbol"),
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        _emit(GraphService().callees(Path(segment), symbol), json_output)
    except GraphCommandError as exc:
        _handle_graph_error(exc, json_output)
