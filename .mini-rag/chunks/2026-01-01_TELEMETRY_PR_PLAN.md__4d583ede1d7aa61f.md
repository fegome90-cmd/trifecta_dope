for search)
        )

    except Exception as e:
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

        telemetry.event(
            "ctx.search",
            {"query": query, "limit": limit},
            {"status": "error", "error": str(e)},
            elapsed_ms,
            bytes_read=getattr(file_system, 'total_bytes_read', 0),  # NEW
        )
        typer.echo(_format_error(e, "Search Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()
```
