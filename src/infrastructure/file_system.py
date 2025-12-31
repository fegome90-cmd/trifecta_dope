"""File System Adapter for Trifecta operations."""

from pathlib import Path

from typing import TYPE_CHECKING

from src.domain.models import TrifectaPack

if TYPE_CHECKING:
    from src.domain.models import TrifectaConfig


class FileSystemAdapter:
    """Handles file system operations for Trifecta."""

    def save_trifecta(self, target_path: Path, pack: TrifectaPack) -> None:
        """Save a Trifecta pack to disk."""
        ctx_dir = target_path / "_ctx"
        ctx_dir.mkdir(parents=True, exist_ok=True)

        skill_path = target_path / "skill.md"
        readme_path = target_path / "readme_tf.md"
        prime_path = ctx_dir / f"prime_{pack.config.segment}.md"
        agent_path = ctx_dir / "agent.md"
        session_path = ctx_dir / f"session_{pack.config.segment}.md"

        skill_path.write_text(pack.skill_content)
        readme_path.write_text(pack.readme_content)
        prime_path.write_text(pack.prime_content)
        agent_path.write_text(pack.agent_content)
        session_path.write_text(pack.session_content)

    def scan_docs(
        self,
        scan_path: Path,
        repo_root: Path,
        limit: int = 10,
    ) -> list[str]:
        """Scan a directory for markdown docs."""
        if not scan_path.exists():
            return []

        docs = [str(p.relative_to(repo_root)) for p in scan_path.glob("**/*.md")]
        return sorted(docs)[:limit]

    def load_trifecta_config(self, segment_path: Path) -> "TrifectaConfig | None":
        """
        Load TrifectaConfig from _ctx/trifecta_config.json.
        Returns None if file is missing.
        Raises ValueError if file exists but is invalid (Fail-Closed).
        """
        import json
        from src.domain.models import TrifectaConfig

        config_path = segment_path / "_ctx" / "trifecta_config.json"

        if not config_path.exists():
            return None

        try:
            content = config_path.read_text()
            data = json.loads(content)
            return TrifectaConfig(**data)
        except Exception:
            # Deterministic strict error (fail-closed)
            raise ValueError("Failed Constitution: trifecta_config.json is invalid")
