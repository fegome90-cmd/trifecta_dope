"""Tripwire: Search finds terms beyond 500 chars (mandatory preview 600+)."""

from src.application.context_service import ContextService
from src.application.use_cases import PREVIEW_LENGTH


def test_ctx_search_finds_telemetry_beyond_500_preview(tmp_path):
    """
    Tripwire: 'telemetry' term at byte 555 in repo_map.md must be discoverable.

    Regression guard: If PREVIEW_LENGTH < 600, this test will FAIL.
    Baseline evidence shows 'telemetry' at byte 555 in repo_map.md.
    """
    # Setup: Create test segment with synthetic repo_map where telemetry is buried
    segment_root = tmp_path / "test_segment"
    segment_root.mkdir()
    ctx_dir = segment_root / "_ctx"
    ctx_dir.mkdir()

    # Simulate repo_map.md structure where "telemetry" appears at ~580 chars
    buried_content = (
        "# Trifecta Dope - Repository Map\n\n"
        "> **Generated**: __DATE__\n"
        "> **Purpose**: High-level module navigation\n\n"
        "---\n\n"
        "## Module Overview\n\n"
        "| Module | Path | Purpose |\n"
        "|--------|------|----------||\n"
        "| Application | `src/application/` | Application layer |\n\n"
        "---\n\n"
        "## Clean Architecture Layers\n\n"
        "```\n"
        + "A"
        * 400  # Padding to push "telemetry" beyond 500 but within 1000
        + "\n```\n\n"
        "[Infrastructure Layer] - CLI, File System, Telemetry\n"  # ~580 chars
    )

    context_pack = {
        "schema_version": 1,
        "segment": "test_segment",
        "created_at": "2026-01-03T00:00:00",
        "digest": "",
        "source_files": [],
        "chunks": [
            {
                "id": "test:repo_map_buried",
                "doc": "test",
                "title_path": ["repo_map.md"],
                "text": buried_content,
                "char_count": len(buried_content),
                "token_est": len(buried_content) // 4,
                "source_path": "repo_map.md",
                "chunking_method": "whole_file",
            }
        ],
        "index": [
            {
                "id": "test:repo_map_buried",
                "title_path_norm": "repo_map.md",
                "preview": buried_content[:PREVIEW_LENGTH].strip() + "...",
                "token_est": len(buried_content) // 4,
            }
        ],
    }

    pack_path = ctx_dir / "context_pack.json"
    import json

    pack_path.write_text(json.dumps(context_pack, indent=2))

    # Verify precondition: term IS beyond 500 chars
    first_telemetry = buried_content.find("Telemetry")
    assert first_telemetry > 500, (
        f"Test setup error: 'Telemetry' should be beyond 500 chars, found at {first_telemetry}"
    )

    # Execute: Search for buried term
    service = ContextService(segment_root)
    result = service.search("telemetry", k=5)

    # Verify: Term MUST be found with PREVIEW_LENGTH >= 1000
    ids = [hit.id for hit in result.hits]
    assert "test:repo_map_buried" in ids, (
        f"FAIL: 'telemetry' at byte {first_telemetry} not found. PREVIEW_LENGTH={PREVIEW_LENGTH} insufficient."
    )


def test_preview_length_constant_is_enforced():
    """
    Tripwire: PREVIEW_LENGTH constant must be >= 1000 to capture buried terms.

     This test prevents accidental reduction of PREVIEW_LENGTH value.
     Evidence: 'telemetry' in repo_map.md appears at byte 945.
    """
    from src.application.use_cases import PREVIEW_LENGTH

    assert PREVIEW_LENGTH >= 1000, (
        f"PREVIEW_LENGTH={PREVIEW_LENGTH} is too small. Must be >= 1000 to capture 'telemetry' at byte 945."
    )

    # Additional: Verify it's an integer (type safety)
    assert isinstance(PREVIEW_LENGTH, int), (
        f"PREVIEW_LENGTH must be int, got {type(PREVIEW_LENGTH)}"
    )
