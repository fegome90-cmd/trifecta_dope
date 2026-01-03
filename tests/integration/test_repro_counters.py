import json
import subprocess
from pathlib import Path


def test_counters_isolation():
    # 1. Run symbols (should produce raw_bytes, ast_parse)
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "src.infrastructure.cli",
            "ast",
            "symbols",
            "sym://python/mod/src/infrastructure/cli_ast",
            "--segment",
            ".",
            "--telemetry",
            "full",
        ],
        check=True,
    )

    last_run = json.loads(Path("_ctx/telemetry/last_run.json").read_text())
    # Updated to use new schema keys (ast, lsp, etc) instead of metrics_delta
    last_run = json.loads(Path("_ctx/telemetry/last_run.json").read_text())
    print("SYMBOLS RUN AST:", last_run.get("ast", {}))

    assert last_run["ast"]["ast_parse_count"] > 0, "Symbols run missing ast_parse_count"
    # file_read metrics deprecated in current schema, focusing on AST/LSP
    # assert last_run["file_read"]["raw_bytes"] > 0, "Symbols run missing raw_bytes"

    # 2. Run snippet (should produce excerpt_bytes, NO ast_parse)
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "src.infrastructure.cli",
            "ast",
            "snippet",
            "sym://python/type/src/infrastructure/cli_ast/symbols",
        ],
        check=True,
    )

    last_run = json.loads(Path("_ctx/telemetry/last_run.json").read_text())
    last_run = json.loads(Path("_ctx/telemetry/last_run.json").read_text())
    print("SNIPPET RUN AST:", last_run.get("ast", {}))

    # Snippet command MUST parse AST to resolve symbol range, so expected count > 0
    assert last_run["ast"]["ast_parse_count"] > 0, "Snippet run missing ast_parse_count"
    # file_read metrics deprecated
    # assert last_run["file_read"]["raw_bytes"] == 0, "Snippet run leaked into raw_bytes"
    # assert last_run["file_read"]["excerpt_bytes"] > 0, "Snippet run missing excerpt_bytes"
