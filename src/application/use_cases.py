"""Use Cases for Trifecta operations."""
from pathlib import Path
from typing import Optional

from src.domain.models import TrifectaConfig, TrifectaPack, ValidationResult
from src.domain.constants import MAX_SKILL_LINES
from src.infrastructure.templates import TemplateRenderer
from src.infrastructure.file_system import FileSystemAdapter


class CreateTrifectaUseCase:
    """Create a new Trifecta pack."""

    def __init__(
        self,
        template_renderer: TemplateRenderer,
        file_system: FileSystemAdapter,
    ):
        self.template_renderer = template_renderer
        self.file_system = file_system

    def execute(
        self,
        config: TrifectaConfig,
        target_path: Path,
        docs: list[str],
        dry_run: bool = False,
    ) -> TrifectaPack:
        """Generate and save a Trifecta pack.

        Args:
            config: Trifecta configuration
            target_path: Target directory path
            docs: List of documentation files
            dry_run: If True, generate but don't save files

        Returns:
            TrifectaPack with generated content
        """
        pack = TrifectaPack(
            config=config,
            skill_content=self.template_renderer.render_skill(config),
            prime_content=self.template_renderer.render_prime(config, docs),
            agent_content=self.template_renderer.render_agent(config),
            session_content=self.template_renderer.render_session(config),
            readme_content=self.template_renderer.render_readme(config),
        )

        # Validate before saving
        if pack.skill_line_count > MAX_SKILL_LINES:
            raise ValueError(
                f"skill.md exceeds {MAX_SKILL_LINES} lines ({pack.skill_line_count})"
            )

        # Save files (skip if dry_run)
        if not dry_run:
            self.file_system.save_trifecta(target_path, pack)

        return pack


class ValidateTrifectaUseCase:
    """Validate an existing Trifecta pack."""

    def __init__(self, file_system: FileSystemAdapter):
        self.file_system = file_system

    def execute(self, target_path: Path) -> ValidationResult:
        """Validate a Trifecta pack structure and content."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check skill.md
        skill_path = target_path / "skill.md"
        if not skill_path.exists():
            errors.append("Missing: skill.md")
        else:
            content = skill_path.read_text()
            line_count = len(content.strip().split("\n"))
            if line_count > MAX_SKILL_LINES:
                errors.append(f"skill.md exceeds {MAX_SKILL_LINES} lines ({line_count})")

        # Check _ctx directory
        ctx_dir = target_path / "_ctx"
        if not ctx_dir.exists():
            errors.append("Missing: _ctx/ directory")
        else:
            prime_files = list(ctx_dir.glob("prime_*.md"))
            if not prime_files:
                errors.append("Missing: _ctx/prime_*.md")

            agent_path = ctx_dir / "agent.md"
            if not agent_path.exists():
                errors.append("Missing: _ctx/agent.md")

            session_files = list(ctx_dir.glob("session_*.md"))
            if not session_files:
                warnings.append("Missing: _ctx/session_*.md (optional but recommended)")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class RefreshPrimeUseCase:
    """Refresh prime_*.md by re-scanning docs."""

    def __init__(
        self,
        template_renderer: TemplateRenderer,
        file_system: FileSystemAdapter,
    ):
        self.template_renderer = template_renderer
        self.file_system = file_system

    def execute(
        self,
        target_path: Path,
        scan_path: Path,
        repo_root: Path,
    ) -> str:
        """Re-scan docs and update prime file."""
        ctx_dir = target_path / "_ctx"
        prime_files = list(ctx_dir.glob("prime_*.md"))

        if not prime_files:
            raise FileNotFoundError("No prime_*.md found. Run 'create' first.")

        prime_path = prime_files[0]
        segment = prime_path.stem.replace("prime_", "")

        # Scan docs
        docs = self.file_system.scan_docs(scan_path, repo_root)

        # Build minimal config
        config = TrifectaConfig(
            segment=segment,
            scope=f"Segment {segment}",
            repo_root=str(repo_root),
        )

        # Regenerate prime
        prime_content = self.template_renderer.render_prime(config, docs)
        prime_path.write_text(prime_content)

        return prime_path.name
