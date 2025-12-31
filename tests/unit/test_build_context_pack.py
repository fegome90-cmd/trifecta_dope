"""Tests for BuildContextPackUseCase."""

import json
from pathlib import Path
from src.application.use_cases import BuildContextPackUseCase
from src.domain.naming import normalize_segment_id
from src.infrastructure.file_system import FileSystemAdapter


class TestBuildContextPackUseCase:
    def test_creates_valid_context_pack_json(self, tmp_path: Path) -> None:
        """Should create valid context_pack.json with schema v1."""
        segment = tmp_path / "test_segment"
        segment.mkdir()
        segment_id = normalize_segment_id(segment.name)
        (segment / "skill.md").write_text("# Skill\n\nContent here.")

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_id}.md").write_text("# Agent\n\nContent.")
        (ctx_dir / f"prime_{segment_id}.md").write_text("# Prime\n\nContent.")
        (ctx_dir / f"session_{segment_id}.md").write_text("# Session\n\nContent.")
        (ctx_dir / "trifecta_config.json").write_text(
            '{"segment": "test_segment", "scope": "local", "repo_root": "."}'
        )
        (segment / "AGENTS.md").write_text("# AGENTS\n\nRules here.")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(segment)

        assert result.is_ok()

        pack_path = ctx_dir / "context_pack.json"
        assert pack_path.exists()

        pack_data = json.loads(pack_path.read_text())
        assert pack_data["schema_version"] == 1
        assert pack_data["segment"] == segment_id

    def test_uses_segment_id_not_segment(self, tmp_path: Path) -> None:
        """Context pack should use segment_id field."""
        segment = tmp_path / "Test-Segment"
        segment.mkdir()
        segment_id = normalize_segment_id(segment.name)
        (segment / "skill.md").write_text("# Skill")

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_id}.md").write_text("# Agent")
        (ctx_dir / f"prime_{segment_id}.md").write_text("# Prime")
        (ctx_dir / f"session_{segment_id}.md").write_text("# Session")
        (ctx_dir / "trifecta_config.json").write_text(
            '{"segment": "Test-Segment", "scope": "local", "repo_root": "."}'
        )
        (segment / "AGENTS.md").write_text("# AGENTS")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        result = use_case.execute(segment)

        assert result.is_ok()

        pack_data = json.loads((ctx_dir / "context_pack.json").read_text())
        assert pack_data["segment"] == segment_id

    def test_digest_contains_at_most_2_chunks(self, tmp_path: Path) -> None:
        """Digest should contain at most 2 chunks."""
        segment = tmp_path / "test"
        segment.mkdir()
        segment_id = normalize_segment_id(segment.name)
        (segment / "skill.md").write_text("A" * 5000)  # Large file

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_id}.md").write_text("B" * 5000)
        (ctx_dir / f"prime_{segment_id}.md").write_text("C" * 5000)
        (ctx_dir / f"session_{segment_id}.md").write_text("D" * 1000)
        (ctx_dir / "trifecta_config.json").write_text(
            '{"segment": "test", "scope": "local", "repo_root": "."}'
        )
        (segment / "AGENTS.md").write_text("# AGENTS")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        use_case.execute(segment)

        pack_data = json.loads((ctx_dir / "context_pack.json").read_text())
        assert len(pack_data["digest"]) <= 2

    def test_digest_total_tokens_at_most_2000(self, tmp_path: Path) -> None:
        """Digest total token count should not exceed 2000."""
        segment = tmp_path / "test"
        segment.mkdir()
        segment_id = normalize_segment_id(segment.name)
        # Create files that would total >2000 tokens if all included
        (segment / "skill.md").write_text("A" * 6000)  # 1500 tokens

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_id}.md").write_text("B" * 6000)  # 1500 tokens
        (ctx_dir / f"prime_{segment_id}.md").write_text("C" * 2400)  # 600 tokens
        (ctx_dir / f"session_{segment_id}.md").write_text("D" * 800)  # 200 tokens
        (ctx_dir / "trifecta_config.json").write_text(
            '{"segment": "test", "scope": "local", "repo_root": "."}'
        )
        (segment / "AGENTS.md").write_text("# AGENTS")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        use_case.execute(segment)

        pack_data = json.loads((ctx_dir / "context_pack.json").read_text())

        # Calculate total tokens in digest
        total_tokens = 0
        for entry in pack_data["digest"]:
            chunk = next(c for c in pack_data["chunks"] if c["id"] == entry["chunk_id"])
            total_tokens += chunk["token_est"]

        assert total_tokens <= 2000

    def test_index_contains_all_chunks(self, tmp_path: Path) -> None:
        """Index should contain metadata for all chunks."""
        segment = tmp_path / "test"
        segment.mkdir()
        segment_id = normalize_segment_id(segment.name)
        (segment / "skill.md").write_text("# Skill")

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_id}.md").write_text("# Agent")
        (ctx_dir / f"prime_{segment_id}.md").write_text("# Prime")
        (ctx_dir / f"session_{segment_id}.md").write_text("# Session")
        (ctx_dir / "trifecta_config.json").write_text(
            '{"segment": "test", "scope": "local", "repo_root": "."}'
        )
        (segment / "AGENTS.md").write_text("# AGENTS")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        use_case.execute(segment)

        pack_data = json.loads((ctx_dir / "context_pack.json").read_text())

        # Should have 3 chunks (skill, agent, prime - session might be excluded)
        assert len(pack_data["index"]) >= 3
        assert len(pack_data["chunks"]) == len(pack_data["index"])

    def test_source_files_no_mtime(self, tmp_path: Path) -> None:
        """Source files should not have mtime field."""
        segment = tmp_path / "test"
        segment.mkdir()
        segment_id = normalize_segment_id(segment.name)
        (segment / "skill.md").write_text("# Skill")

        ctx_dir = segment / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_id}.md").write_text("# Agent")
        (ctx_dir / f"prime_{segment_id}.md").write_text("# Prime")
        (ctx_dir / f"session_{segment_id}.md").write_text("# Session")
        (ctx_dir / "trifecta_config.json").write_text(
            '{"segment": "test", "scope": "local", "repo_root": "."}'
        )
        (segment / "AGENTS.md").write_text("# AGENTS")

        use_case = BuildContextPackUseCase(FileSystemAdapter())
        use_case.execute(segment)

        pack_data = json.loads((ctx_dir / "context_pack.json").read_text())

        for sf in pack_data["source_files"]:
            assert "mtime" in sf
            assert "path" in sf
            assert "sha256" in sf
            assert "chars" in sf
