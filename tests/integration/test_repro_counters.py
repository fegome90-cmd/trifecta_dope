import json
import subprocess
from pathlib import Path
import pytest


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
    print("SYMBOLS RUN:", last_run["metrics_delta"])

    assert last_run["ast"]["ast_parse_count"] > 0, "Symbols run missing ast_parse_count"
    assert last_run["file_read"]["raw_bytes"] > 0, "Symbols run missing raw_bytes"
    assert last_run["file_read"]["excerpt_bytes"] == 0, "Symbols run leaked into excerpt_bytes"

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
            "--segment",
            ".",
            "--telemetry",
            "full",
        ],
        check=True,
    )

    last_run = json.loads(Path("_ctx/telemetry/last_run.json").read_text())
    print("SNIPPET RUN:", last_run["metrics_delta"])

    assert last_run["ast"]["ast_parse_count"] == 0, "Snippet run incorrectly has ast_parse_count"
    assert last_run["file_read"]["raw_bytes"] == 0, "Snippet run leaked into raw_bytes"
    assert last_run["file_read"]["excerpt_bytes"] > 0, "Snippet run missing excerpt_bytes"
