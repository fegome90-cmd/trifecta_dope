```python
# src/infrastructure/cli.py
@session_app.command("query")
def session_query(
    segment: str = typer.Option(..., "-s"),
    type: str = typer.Option(None, "--type"),
    last: int = typer.Option(None, "--last"),
    since: str = typer.Option(None, "--since"),
    tag: str = typer.Option(None, "--tag"),
    outcome: str = typer.Option(None, "--outcome"),
    format: str = typer.Option("clean", "--format")
):
    """Query session entries from telemetry."""
    import subprocess

    # Use grep for performance (filter early)
    grep_result = subprocess.run(
        ["grep", '"cmd": "session.entry"', f"{segment}/_ctx/telemetry/events.jsonl"],
        capture_output=True, text=True
    )

    entries = []
    for line in grep_result.stdout.splitlines():
        event = json.loads(line)

        # Apply filters
        if type and event["args"].get("type") != type:
            continue
        if outcome and event["result"].get("outcome") != outcome:
            continue
        if tag and tag not in event["x"].get("tags", []):
            continue

        # Format output
        if format == "clean":
            entry = {
                "ts": event["ts"],
                "summary": event["args"]["summary"],
                "type": event["args"]["type"],
                "files": event["args"].get("files", []),
                "commands": event["args"].get("commands", []
