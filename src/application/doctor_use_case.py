"""Doctor Use Case - Diagnose segment issues using SegmentRef as SSOT."""

from dataclasses import dataclass
from pathlib import Path

from src.domain.segment_resolver import SegmentRef, resolve_segment_ref


HEALTHY_THRESHOLD = 70


@dataclass(frozen=True)
class DoctorDiagnosis:
    """Diagnosis result for a segment."""

    segment_ref: SegmentRef
    issues: list[str]
    warnings: list[str]
    health_score: int


class DoctorUseCase:
    """Use case for diagnosing segment issues."""

    def execute(self, repo_path: str | Path) -> DoctorDiagnosis:
        """Execute diagnosis for a segment.

        Args:
            repo_path: Path to the segment root

        Returns:
            DoctorDiagnosis with found issues and warnings
        """
        segment_ref = resolve_segment_ref(repo_path)
        root = segment_ref.root_abs

        issues: list[str] = []
        warnings: list[str] = []

        ctx_dir = root / "_ctx"
        if not ctx_dir.exists():
            issues.append(f"Missing _ctx directory at {ctx_dir}")
        else:
            prime_files = list(ctx_dir.glob("prime_*.md"))
            if not prime_files:
                issues.append("Missing prime_*.md file in _ctx/")

            agent_files = list(ctx_dir.glob("agent*.md"))
            if not agent_files:
                warnings.append("Missing agent*.md file in _ctx/")

            context_pack = ctx_dir / "context_pack.json"
            if not context_pack.exists():
                warnings.append("Missing context_pack.json - run 'trifecta ctx build'")

        skill_path = root / "skill.md"
        if not skill_path.exists():
            warnings.append("Missing skill.md at segment root")

        telemetry_dir = ctx_dir / "telemetry" if ctx_dir.exists() else None
        if telemetry_dir and telemetry_dir.exists():
            events_file = telemetry_dir / "events.jsonl"
            if not events_file.exists():
                warnings.append("No telemetry events recorded yet")

        health_score = self._calculate_health_score(issues, warnings)

        return DoctorDiagnosis(
            segment_ref=segment_ref,
            issues=issues,
            warnings=warnings,
            health_score=health_score,
        )

    def _calculate_health_score(self, issues: list[str], warnings: list[str]) -> int:
        """Calculate health score based on issues and warnings."""
        score = 100
        score -= len(issues) * 25
        score -= len(warnings) * 10
        return max(0, score)
