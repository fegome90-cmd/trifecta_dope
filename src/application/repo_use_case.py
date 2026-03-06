"""Repo Use Case - Register/List/Show repositories using SegmentRef as SSOT."""

import json
from dataclasses import dataclass
from pathlib import Path

from src.domain.segment_resolver import resolve_segment_ref


REGISTRY_FILE = "trifecta_repos.json"


@dataclass(frozen=True)
class RepoEntry:
    """A registered repository entry."""

    repo_id: str
    path: str
    slug: str
    fingerprint: str


class RepoUseCase:
    """Use case for managing repository registry."""

    def __init__(self, registry_path: Path | None = None):
        """Initialize RepoUseCase.

        Args:
            registry_path: Optional path to registry file. Defaults to ~/.trifecta/repos.json
        """
        if registry_path is None:
            registry_path = Path.home() / ".trifecta" / REGISTRY_FILE
        self._registry_path = registry_path

    def register(self, repo_path: str | Path) -> RepoEntry:
        """Register a repository.

        Args:
            repo_path: Path to the repository root

        Returns:
            RepoEntry with registration details
        """
        segment_ref = resolve_segment_ref(repo_path)
        root = segment_ref.root_abs

        if not root.exists():
            raise FileNotFoundError(f"Repository path does not exist: {root}")

        entry = RepoEntry(
            repo_id=segment_ref.id,
            path=str(root),
            slug=segment_ref.slug,
            fingerprint=segment_ref.fingerprint,
        )

        self._save_entry(entry)
        return entry

    def list_repos(self) -> list[RepoEntry]:
        """List all registered repositories.

        Returns:
            List of RepoEntry objects
        """
        if not self._registry_path.exists():
            return []

        try:
            data = json.loads(self._registry_path.read_text())
        except (json.JSONDecodeError, IOError):
            return []

        repos = []
        for item in data.get("repos", []):
            repos.append(
                RepoEntry(
                    repo_id=item["repo_id"],
                    path=item["path"],
                    slug=item["slug"],
                    fingerprint=item["fingerprint"],
                )
            )
        return repos

    def show(self, repo_id: str) -> RepoEntry | None:
        """Show details of a specific repository.

        Args:
            repo_id: The repository ID (slug_fingerprint format)

        Returns:
            RepoEntry if found, None otherwise
        """
        repos = self.list_repos()
        for repo in repos:
            if repo.repo_id == repo_id:
                return repo
        return None

    def _save_entry(self, entry: RepoEntry) -> None:
        """Save entry to registry."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)

        repos = self.list_repos()

        existing = [r for r in repos if r.repo_id != entry.repo_id]
        existing.append(entry)

        data = {"repos": [vars(r) for r in existing]}
        self._registry_path.write_text(json.dumps(data, indent=2))
