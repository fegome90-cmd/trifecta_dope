"ctx.get",
            {"ids": id_list, "mode": mode, "budget": budget_token_est},
            {"chunks_returned": output.count("---"), "status": "ok"},
            elapsed_ms,
            bytes_read=bytes_read,        # NEW
            disclosure_mode=mode,         # NEW
        )

    except Exception as e:
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

        telemetry.event(
            "ctx.get",
            {"ids": id_list, "mode": mode},
            {"status": "error", "error": str(e)},
            elapsed_ms,
            bytes_read=getattr(file_system, 'total_bytes_read', 0),  # NEW
            disclosure_mode=mode,  # NEW
        )
        typer.echo(_format_error(e, "Get Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()
```
