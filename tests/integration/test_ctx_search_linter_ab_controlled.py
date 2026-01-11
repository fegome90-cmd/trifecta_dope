"""Integration test for Query Linter A/B controlled.

This test verifies that the query linter expansion (TRIFECTA_LINT=1)
converts vague queries into guided queries, resulting in hits that
would otherwise be zero.

A/B Evidence:
- Query: "servicio" (Spanish, vague, 1 token)
- OFF (TRIFECTA_LINT=0): 0 hits
- ON  (TRIFECTA_LINT=1): 1+ hits (expanded via alias 'servicio' -> 'ContextService')
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def ab_segment(tmp_path: Path) -> Path:
    """Create a minimal segment with context_pack.json for A/B testing."""
    segment = tmp_path / "ab_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)

    # Create context pack with schema v1
    context_pack = {
        "schema_version": 1,
        "segment": "ab_segment",
        "created_at": "2026-01-05T18:00:00Z",
        "digest": "Test segment for A/B linter validation",
        "source_files": [],
        "chunks": [
            {
                "id": "agent:abc123",
                "doc": "agent",
                "title_path": ["agent.md"],
                "text": "ContextService is the core component for managing context in the system.",
                "char_count": 73,
                "token_est": 15,
                "source_path": "agent.md",
                "chunking_method": "whole_file",
            }
        ],
        "index": [
            {
                "id": "agent:abc123",
                "title_path_norm": "agent.md",
                "preview": "ContextService is the core component...",
                "token_est": 15,
            }
        ],
    }

    (ctx_dir / "context_pack.json").write_text(json.dumps(context_pack, indent=2))

    # Create configs
    configs_dir = segment / "configs"
    configs_dir.mkdir()

    (configs_dir / "anchors.yaml").write_text(
        "strong:\n  - ContextService\n  - agent.md\nweak:\n  - docs\n  - .md\n"
    )

    aliases = "aliases:\n  - pattern: servicio\n    canonical: ContextService\n"
    (configs_dir / "aliases.yaml").write_text(aliases)

    return segment


def run_search(segment: Path, query: str, lint: bool) -> tuple[int, list[str]]:
    """Run ctx search and return (hit_count, chunk_ids)."""
    env = os.environ.copy()
    env["TRIFECTA_LINT"] = "1" if lint else "0"

    result = subprocess.run(
        [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "search",
            "--segment",
            str(segment),
            "--query",
            query,
            "--limit",
            "5",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path(__file__).parent.parent.parent),
    )

    output = result.stdout + result.stderr

    # Parse hits from output
    if "No results found" in output:
        return 0, []

    # Extract hit count from "Search Results (N hits):"
    import re

    match = re.search(r"Search Results \((\d+) hits?\)", output)
    hit_count = int(match.group(1)) if match else 0

    # Extract chunk IDs [id]
    chunk_ids = re.findall(r"\[([a-z]+:[a-z0-9]+)\]", output)

    return hit_count, chunk_ids


class TestQueryLinterABControlled:
    """A/B controlled tests for query linter expansion."""

    def test_vague_spanish_query_off_zero_hits(self, ab_segment: Path):
        """OFF: Vague Spanish query 'servicio' returns 0 hits without expansion."""
        hits, ids = run_search(ab_segment, "servicio", lint=False)
        assert hits == 0, f"Expected 0 hits with LINT=OFF, got {hits}"
        assert len(ids) == 0

    def test_vague_spanish_query_on_hits_via_expansion(self, ab_segment: Path):
        """ON: Vague Spanish query 'servicio' returns hits via alias expansion."""
        hits, ids = run_search(ab_segment, "servicio", lint=True)
        assert hits > 0, f"Expected >0 hits with LINT=ON, got {hits}"
        assert "agent:abc123" in ids, f"Expected agent:abc123 in ids, got {ids}"

    def test_ab_delta_positive(self, ab_segment: Path):
        """A/B delta: ON hits > OFF hits for vague queries."""
        hits_off, _ = run_search(ab_segment, "servicio", lint=False)
        hits_on, ids_on = run_search(ab_segment, "servicio", lint=True)

        delta = hits_on - hits_off
        assert delta > 0, f"Expected positive delta (ON > OFF), got {delta}"
        assert "agent:abc123" in ids_on
