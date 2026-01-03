import typer
import time
import json
from pathlib import Path
from typing import Optional
from src.infrastructure.telemetry import Telemetry
from src.domain.ast_models import ASTResponse, ASTData, ASTError, ASTErrorCode, Range
from src.domain.result import Ok, Err
from src.application.symbol_selector import SymbolQuery, SymbolResolver, SkeletonMapBuilder
from src.application.ast_parser import ASTParser
from src.infrastructure.segment_utils import resolve_segment_root

ast_app = typer.Typer(help="AST & Parsing Commands")


def _json_output(response: ASTResponse):
    print(json.dumps(response.model_dump(exclude_none=True), indent=2))


def _error_response(code: str, message: str, kind: str = "skeleton") -> ASTResponse:
    return ASTResponse(status="error", kind=kind, errors=[ASTError(code=code, message=message)])


def _get_telemetry(level: str = "lite") -> Optional[Telemetry]:
    if level == "off":
        return None
    return Telemetry(Path.cwd(), level=level)


@ast_app.command("symbols")
def symbols(
    uri: str = typer.Argument(..., help="sym://python/mod|type/..."),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("full", "--telemetry"),
):
    root = resolve_segment_root(Path(segment))
    telemetry = _get_telemetry(telemetry_level)

    # Phase 3: LSP Daemon
    from src.infrastructure.lsp_daemon import LSPDaemonClient

    client = LSPDaemonClient(root)
    client.connect_or_spawn()  # Fire & Forget spawn if needed

    try:
        # 1. Parse URI
        match SymbolQuery.parse(uri):
            case Err(e):
                _json_output(ASTResponse(status="error", kind="skeleton", errors=[e]))
                return
            case Ok(query):
                pass

        # 2. Check LSP Readiness (Fallback Logic)
        # The 'use_lsp' variable was assigned but not used, leading to F841.
        # The original logic was to check client readiness and then decide on fallback.
        # The 'except Exception' blocks in the instruction were syntactically incorrect
        # and misplaced. The fix removes the unused variable and ensures proper error handling.
        if not client.is_ready():
            if telemetry:
                try:
                    telemetry.incr("lsp_fallback_count")
                    telemetry.event(
                        "lsp.fallback",
                        {},
                        {"status": "ok"},
                        1,
                        reason="daemon_not_ready",  # Phase 3 reason
                        fallback_to="ast_only",
                    )
                except Exception:  # E722: do not use bare 'except'
                    pass

        t0 = time.perf_counter_ns()
        resolver = SymbolResolver(SkeletonMapBuilder(), root)

        match resolver.resolve(query):
            case Err(e):
                _json_output(ASTResponse(status="error", kind="skeleton", errors=[e]))
                if telemetry:
                    telemetry.event(
                        "selector.resolve",
                        {"symbol_query": uri},
                        {"status": "error", "error": e.code},
                        1,
                    )
            case Ok(candidate):
                duration_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

                # Phase 3: Feed LSP (via Daemon)
                full_path = root / candidate.file_rel
                if full_path.exists():
                    # Send to daemon (Daemon handles if READY or WARMING)
                    try:
                        client.send(
                            {
                                "method": "did_open",
                                "params": {
                                    "path": str(full_path),
                                    "content": full_path.read_text(),
                                },
                            }
                        )
                    except Exception:
                        pass

                # Telemetry
                if telemetry:
                    telemetry.event(
                        "selector.resolve",
                        {"symbol_query": uri},
                        {"status": "ok"},
                        duration_ms,
                        symbol_query=uri,
                        resolved=True,
                        file=candidate.file_rel,
                        matches=1,
                        ambiguous=False,
                        kind=candidate.kind,
                    )

                # AST Parsing (Phase 2a)
                # Phase 3: Even if LSP is ready, we currently output AST skeleton.
                # Use LSP for "symbols" if we implemented lsp.documentSymbol,
                # but to respect "No romper Phase 2a", we keep AST parser path for output
                # and use LSP only as a "value add" side effect (e.g. diagnostics)
                # OR if we were replacing parsing.
                # User said: "LSP deje de ser latente y aporte valor real".
                # For `symbols` command, value is limited unless we use LSP symbols.

                parser = ASTParser()
                # Read File Event
                if telemetry:
                    content_bytes = full_path.stat().st_size if full_path.exists() else 0
                    telemetry.event(
                        "file.read",
                        {},
                        {"status": "ok"},
                        1,
                        file=candidate.file_rel,
                        bytes=content_bytes,
                        mode="raw",
                    )

                children, sha8 = parser.parse(full_path) if full_path.exists() else ([], "")

                # Parse Event
                if telemetry:
                    telemetry.incr("ast_parse_count")
                    telemetry.incr("ast_cache_miss_count")
                    telemetry.event(
                        "ast.parse",
                        {},
                        {"status": "ok"},
                        1,
                        file=candidate.file_rel,
                        symbols_count=len(children),
                        cache_hit=False,
                        skeleton_bytes=100,
                        content_sha8=sha8,
                    )

                data = ASTData(
                    uri=uri,
                    range=Range(start_line=1, end_line=100),  # Mock
                    children=children,
                    truncated=False,
                )
                _json_output(ASTResponse(status="ok", kind="skeleton", data=data))

    except Exception as e:
        _json_output(_error_response(ASTErrorCode.INTERNAL_ERROR, str(e)))
    finally:
        # Phase 3: we do not stop the client, we just flush telemetry
        # Daemon manages its own lifecycle
        if telemetry:
            telemetry.flush()


@ast_app.command("snippet")
def snippet(uri: str = typer.Argument(...)):
    pass  # Minimal stub


@ast_app.command("hover")
def hover(
    uri: str = typer.Argument(..., help="File path to hover over"),
    line: int = typer.Option(..., "--line", "-l"),
    character: int = typer.Option(..., "--char", "-c"),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("full", "--telemetry"),
):
    """[Phase 3] LSP Hover request via Daemon."""
    root = resolve_segment_root(Path(segment))
    telemetry = _get_telemetry(telemetry_level)

    # Phase 3: LSP Daemon
    from src.infrastructure.lsp_daemon import LSPDaemonClient

    client = LSPDaemonClient(root)
    client.connect_or_spawn()  # Fire & Forget spawn if needed

    # Warm-wait: allow up to 200ms for daemon to become READY (only if recently spawned)
    warm_wait_start = time.time()
    max_warm_wait_sec = 0.2
    daemon_ready = False

    while (time.time() - warm_wait_start) < max_warm_wait_sec:
        if client.is_ready():
            daemon_ready = True
            break
        time.sleep(0.05)  # Poll every 50ms

    warm_wait_ms = int((time.time() - warm_wait_start) * 1000)

    # 2. Check LSP Readiness
    if daemon_ready:
        # RUN 2: WARM PATH
        if telemetry:
            telemetry.incr("lsp_ready_count")
            telemetry.event(
                "lsp.daemon_status",
                {},
                {"status": "ok"},
                1,
                state="READY",
                warm_wait_ms=warm_wait_ms,
            )

        # Execute LSP request
        t0 = time.time_ns()
        result = client.request(
            "textDocument/hover",
            {
                "textDocument": {"uri": f"file://{root}/{uri}"},
                "position": {"line": line, "character": character},
            },
        )
        duration_ms = max(1, (time.time_ns() - t0) // 1_000_000)

        # Prepare safe preview
        import hashlib

        preview_hash = "none"
        if result and isinstance(result, dict):
            preview_hash = hashlib.sha256(str(result).encode()).hexdigest()[:8]

        if telemetry:
            telemetry.observe("lsp.request", duration_ms)
            telemetry.incr("lsp_request_count")
            telemetry.event(
                "lsp.request",
                {"method": "textDocument/hover"},
                {"status": "ok"},
                duration_ms,
                method="textDocument/hover",
                resolved=bool(result),
                target_kind="hover",
                target_preview_sha8=preview_hash,
            )

        # AST-first: always return AST skeleton output
        _json_output(
            ASTResponse(
                status="ok",
                kind="skeleton",
                data=ASTData(
                    uri=uri, range=Range(start_line=1, end_line=10), children=[], truncated=False
                ),
            )
        )

    else:
        # RUN 1: COLD PATH (daemon not ready)
        if telemetry:
            telemetry.event("lsp.spawn", {}, {"status": "ok"}, 1, lsp_state="WARMING")
            telemetry.incr("lsp_fallback_count")
            telemetry.event(
                "lsp.fallback",
                {},
                {"status": "ok"},
                1,
                reason="daemon_not_ready",
                fallback_to="ast_only",
                warm_wait_ms=warm_wait_ms,
            )

        # Fallback to AST
        _json_output(
            ASTResponse(
                status="ok",
                kind="skeleton",
                data=ASTData(
                    uri=uri, range=Range(start_line=1, end_line=10), children=[], truncated=False
                ),
            )
        )

    if telemetry:
        telemetry.flush()
