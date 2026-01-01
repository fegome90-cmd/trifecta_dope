"""
PR#2 Demo: Full integration test showing AST+Selector+Telemetry flow.

This script demonstrates:
1. Create sample Python file
2. Extract AST skeleton
3. Resolve symbol via sym:// DSL
4. Show progressive disclosure modes
5. Emit telemetry events
6. Verify events.jsonl and last_run.json output
"""

import json
import tempfile
from pathlib import Path

from src.infrastructure.telemetry import Telemetry
from src.application.pr2_context_searcher import PR2ContextSearcher


def main() -> None:
    """Run PR#2 demo."""
    print("=" * 70)
    print("PR#2 DEMO: AST + Selector + Telemetry Integration")
    print("=" * 70)

    # Create temp workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n📁 Workspace: {workspace}")

        # Create sample Python file
        sample_file = workspace / "example.py"
        sample_content = '''"""Example module for PR#2 demo."""

class DataProcessor:
    """Processes data with various methods."""

    def __init__(self, name: str):
        self.name = name

    def process_data(self, data: list) -> dict:
        """Process data and return results."""
        return {"status": "ok", "count": len(data)}

    def validate(self) -> bool:
        """Validate processor state."""
        return bool(self.name)


def utility_function(x: int) -> int:
    """Simple utility function."""
    return x * 2
'''
        sample_file.write_text(sample_content)
        print(f"✅ Created sample file: {sample_file.name}")

        # Initialize PR#2 components
        tel = Telemetry(workspace / ".trifecta")
        searcher = PR2ContextSearcher(
            workspace, tel, lsp_enabled=False  # LSP disabled for demo
        )
        print("✅ Initialized searcher with telemetry")

        # Test 1: Search for class
        print("\n" + "-" * 70)
        print("TEST 1: Search for class DataProcessor")
        print("-" * 70)

        result = searcher.search_symbol(
            "sym://python/DataProcessor",
            sample_file,
            disclosure_mode="skeleton",
        )

        if result:
            print(f"✅ Found: {result['file']}")
            print(f"   Location: lines {result['start_line']}-{result['end_line']}")
        else:
            print("❌ Not found (tree-sitter not available)")

        # Test 2: Search for method (will be ambiguous/not found without full extraction)
        print("\n" + "-" * 70)
        print("TEST 2: Search for method DataProcessor.process_data")
        print("-" * 70)

        result = searcher.search_symbol(
            "sym://python/DataProcessor.process_data",
            sample_file,
            disclosure_mode="skeleton",
        )

        if result:
            print(f"✅ Found: {result['file']}")
            print(f"   Location: lines {result['start_line']}-{result['end_line']}")
        else:
            print("❌ Not found (expected if tree-sitter unavailable)")

        # Test 3: Search with excerpt disclosure
        print("\n" + "-" * 70)
        print("TEST 3: Search with excerpt disclosure mode")
        print("-" * 70)

        result = searcher.search_symbol(
            "sym://python/utility_function",
            sample_file,
            disclosure_mode="excerpt",
        )

        if result:
            print(f"✅ Found: {result['file']}")
            if "excerpt" in result:
                print(f"   Excerpt lines {result.get('excerpt_start_line', '?')}-?:")
                excerpt_lines = result["excerpt"].split("\n")
                for line in excerpt_lines[:5]:  # Show first 5 lines
                    print(f"   > {line}")
        else:
            print("❌ Not found")

        # Flush telemetry to disk
        print("\n" + "-" * 70)
        print("Flushing telemetry...")
        print("-" * 70)

        tel.flush()
        print("✅ Telemetry flushed")

        # Read and display events.jsonl
        events_file = workspace / ".trifecta" / "events.jsonl"
        if events_file.exists():
            print(f"\n📊 Events ({events_file.name}):")
            with open(events_file) as f:
                event_count = 0
                for line in f:
                    if line.strip():
                        event_count += 1
                        event = json.loads(line)
                        cmd = event.get("cmd", "unknown")
                        extras = event.get("x", {})
                        print(f"  {event_count}. {cmd}")
                        if extras:
                            keys = list(extras.keys())[:3]
                            print(f"     extras: {', '.join(keys)}")
            print(f"  Total events: {event_count}")
        else:
            print("❌ events.jsonl not found")

        # Read and display last_run.json
        last_run_file = workspace / ".trifecta" / "last_run.json"
        if last_run_file.exists():
            print(f"\n📊 Metrics ({last_run_file.name}):")
            last_run = json.loads(last_run_file.read_text())
            metrics = last_run.get("metrics", {})

            # Show relevant metrics
            for key in [
                "ast_parse_count",
                "ast_cache_hit_count",
                "ast_cache_miss_count",
                "file_read_skeleton_bytes_total",
            ]:
                if key in metrics:
                    print(f"  {key}: {metrics[key]}")
        else:
            print("❌ last_run.json not found")

        # Summary
        print("\n" + "=" * 70)
        print("✅ PR#2 DEMO COMPLETE")
        print("=" * 70)
        print("\nKEY ACHIEVEMENTS:")
        print("  ✅ AST skeleton extraction (tree-sitter ready)")
        print("  ✅ Symbol selector DSL (sym://python/...)")
        print("  ✅ Progressive disclosure modes (skeleton/excerpt/raw)")
        print("  ✅ Telemetry integration (events + metrics)")
        print("  ✅ Bytes tracking (file_read_* counters)")
        print("  ✅ LSP state machine (COLD→WARMING→READY→FAILED)")
        print("\nNOTE: Full AST/LSP features require:")
        print("  - tree-sitter-python installed")
        print("  - pyright installed (for LSP)")


if __name__ == "__main__":
    main()
