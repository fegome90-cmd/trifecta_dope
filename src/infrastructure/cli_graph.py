import json
from pathlib import Path

import typer

from src.application.graph_indexer import GraphIndexer
from src.application.graph_service import GraphService


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
    typer.echo(f"{len(nodes)} result(s)")
    for node in nodes:
        typer.echo(f"- {node['symbol_name']} [{node['kind']}] {node['file_rel']}:{node['line']}")


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
    _emit(GraphService().callers(Path(segment), symbol), json_output)


@graph_app.command("callees")
def callees(
    symbol: str = typer.Option(..., "--symbol"),
    segment: str = typer.Option(".", "--segment", "-s"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    _emit(GraphService().callees(Path(segment), symbol), json_output)
