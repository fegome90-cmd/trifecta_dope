```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields: Any,  # NEW: accept arbitrary kwargs
) -> None:
    """
    Log a discrete event with optional structured fields.

    Args:
        cmd: Command name (e.g., "ctx.search", "ast.parse", "lsp.spawn")
        args: Command arguments (sanitized)
        result: Command result metadata
        timing_ms: Elapsed time in milliseconds (use perf_counter_ns)
        warnings: Optional list of warning messages
        **extra_fields: Additional structured fields (e.g., bytes_read, lsp_state)

    Raises:
        ValueError: If extra_fields contains a reserved key

    Example:
        telemetry.event(
            "lsp.spawn",
            {"pyright_binary": "pyright-langserver"},
            {"pid": 12345, "status": "ok"},
            42,
            lsp_state="WARMING",  # Goes into payload["x"]["lsp_state"]
            spawn_method="subprocess"  # Goes into payload["x"]["spawn_method"]
        )
    """
    if not self.enabled:
        return

    if warnings:
        self.warnings.extend(warnings)

    # NEW: Protect reserved keys
    collision = RESERVED_KEYS & extra_fields.keys()
    if collision:
        raise ValueError(
            f"extra_fields contains reserved keys: {collision}. "
            f"Reserve
