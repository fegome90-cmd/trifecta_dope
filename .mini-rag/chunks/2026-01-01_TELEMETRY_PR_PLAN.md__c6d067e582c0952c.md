```python
@ctx_app.command("get")
def get(
    ids: str = typer.Option(..., "--ids", "-i", help="Comma-separated Chunk IDs"),
    mode: Literal["raw", "excerpt", "skeleton"] = typer.Option("excerpt", "--mode", "-m", help="Disclosure level"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    budget_token_est: int = typer.Option(1500, "--budget-token-est", "-b", help="Max token budget"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Retrieve full content for specific chunks."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_ns = time.perf_counter_ns()  # NEW: monotonic clock
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = GetChunkUseCase(file_system, telemetry)

    id_list = [x.strip() for x in ids.split(",") if x.strip()]

    try:
        output = use_case.execute(
            Path(segment), id_list, mode=mode, budget_token_est=budget_token_est
        )
        typer.echo(output)

        # NEW: Record with monotonic timing
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

        # Collect bytes read from file_system
        bytes_read = getattr(file_system, 'total_bytes_read', 0)

        # Log event with new fields
        telemetry.event(
            "ctx.get",
            {"ids": id_list, "mode": mode, "budget":
