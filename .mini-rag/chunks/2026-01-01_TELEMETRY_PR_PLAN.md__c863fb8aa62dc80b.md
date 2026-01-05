```python
"""Integration tests for AST/LSP telemetry in realistic scenarios."""

import json
from pathlib import Path
import pytest
from src.infrastructure.telemetry import Telemetry
from src.infrastructure.ast_lsp import SkeletonMapBuilder, LSPClient, Selector

class TestSkeletonInstrumentation:
    """Test AST skeleton parsing emits correct telemetry."""

    def test_skeleton_parse_emits_event(self, tmp_path):
        """Verify parse_python() emits ast.parse event."""
        telemetry = Telemetry(tmp_path, level="lite")
        builder = SkeletonMapBuilder(telemetry, tmp_path)

        code = """
def hello():
    pass

class Greeter:
    def greet(self):
        pass
"""

        skeleton = builder.parse_python(code, Path("test.py"))
        telemetry.flush()

        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip().split("\n")[0])

        assert event["cmd"] == "ast.parse"
        assert event["result"]["status"] == "ok"
        assert "skeleton_bytes" in event
        assert "reduction_ratio" in event

    def test_skeleton_cache_tracking(self, tmp_path):
        """Verify cache hits are counted."""
        telemetry = Telemetry(tmp_path, level="lite")
        builder = SkeletonMapBuilder(telemetry, tmp_path)

        code = "def test(): pass"

        # First parse: cache miss
        builder.parse
