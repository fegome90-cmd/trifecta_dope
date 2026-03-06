"""Status Use Case - Show segment status using SegmentRef as SSOT."""

from dataclasses import dataclass
from pathlib import Path

from src.domain.segment_resolver import SegmentRef, resolve_segment_ref


@dataclass(frozen=True)
class SegmentStatus:
    """Status information for a segment."""

    segment_ref: SegmentRef
    has_ctx_dir: bool
    has_context_pack: bool
    has_telemetry: bool
    has_skill_md: bool
    has_prime: bool
    has_agent: bool
    has_session: bool


class StatusUseCase:
    """Use case for showing segment status."""

    def execute(self, repo_path: str | Path) -> SegmentStatus:
        """Execute status check for a segment.

        Args:
            repo_path: Path to the segment root

        Returns:
            SegmentStatus with all checked information
        """
        segment_ref = resolve_segment_ref(repo_path)
        root = segment_ref.root_abs

        ctx_dir = root / "_ctx"
        has_ctx_dir = ctx_dir.exists()

        # Check for context_pack.json
        context_pack = ctx_dir / "context_pack.json" if has_ctx_dir else None
        has_context_pack = context_pack.exists() if context_pack else False

        # Check for telemetry
        telemetry_dir = ctx_dir / "telemetry" if has_ctx_dir else None
        has_telemetry = telemetry_dir.exists() if telemetry_dir else False

        # Check for required files
        skill_path = root / "skill.md"
        has_skill_md = skill_path.exists()

        prime_files = list(ctx_dir.glob("prime_*.md")) if has_ctx_dir else []
        has_prime = len(prime_files) > 0

        agent_files = list(ctx_dir.glob("agent*.md")) if has_ctx_dir else []
        has_agent = len(agent_files) > 0

        session_files = list(ctx_dir.glob("session_*.md")) if has_ctx_dir else []
        has_session = len(session_files) > 0

        return SegmentStatus(
            segment_ref=segment_ref,
            has_ctx_dir=has_ctx_dir,
            has_context_pack=has_context_pack,
            has_telemetry=has_telemetry,
            has_skill_md=has_skill_md,
            has_prime=has_prime,
            has_agent=has_agent,
            has_session=has_session,
        )
