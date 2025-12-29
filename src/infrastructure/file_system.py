"""File System Adapter for Trifecta operations."""
from pathlib import Path

from src.domain.models import TrifectaPack


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

        docs = [
            str(p.relative_to(repo_root))
            for p in scan_path.glob("**/*.md")
        ]
        return sorted(docs)[:limit]
