```python
@ctx_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Search for relevant chunks in the Context Pack."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    start_ns = time.perf_counter_ns()  # NEW: monotonic clock
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = SearchUseCase(file_system, telemetry)

    try:
        output = use_case.execute(Path(segment), query, limit=limit)
        typer.echo(output)

        # NEW: Record with monotonic timing
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

        # Collect bytes read from file_system
        bytes_read = getattr(file_system, 'total_bytes_read', 0)

        # Log event with new fields
        telemetry.event(
            "ctx.search",
            {"query": query, "limit": limit},
            {"hits": output.count("hit"), "status": "ok"},
            elapsed_ms,
            bytes_read=bytes_read,  # NEW
            disclosure_mode=None,   # NEW (N/A for search)
        )

    except Exception as e:
        elapsed_ms
