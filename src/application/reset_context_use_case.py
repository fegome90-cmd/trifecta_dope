"""
Use case for resetting/regenerating context files.

This module provides the business logic for ctx reset command,
separated from CLI concerns (I/O, confirmation prompts).

Note: This is a DESTRUCTIVE operation that overwrites existing files.
Note: Caller is responsible for flushing telemetry (e.g., in finally block).
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.use_cases import BuildContextPackUseCase, ValidateContextPackUseCase
    from src.domain.models import TrifectaConfig
    from src.infrastructure.telemetry import Telemetry
    from src.domain.template_renderer import TemplateRenderer


@dataclass(frozen=True)
class ResetResult:
    """Result of context reset operation."""

    success: bool
    files_written: list[str]
    errors: list[str] = field(default_factory=list)
    validation_passed: bool = True


class ResetContextUseCase:
    """
    Reset/regenerate all context files for a segment.

    This use case:
    1. Loads config from _ctx/trifecta_config.json
    2. Regenerates all template files (skill.md, agent, prime, session, readme)
    3. Runs build to regenerate context_pack.json
    4. Validates the result

    Note: This is a DESTRUCTIVE operation that overwrites existing files.
    """

    def __init__(
        self,
        template_renderer: "TemplateRenderer",
        build_use_case: "BuildContextPackUseCase",
        validate_use_case: "ValidateContextPackUseCase",
        telemetry: "Telemetry",
    ):
        self._template_renderer = template_renderer
        self._build_use_case = build_use_case
        self._validate_use_case = validate_use_case
        self._telemetry = telemetry

    def execute(
        self,
        segment_path: Path,
        config: "TrifectaConfig",
    ) -> ResetResult:
        """
        Execute context reset.

        Args:
            segment_path: Root path of the segment.
            config: TrifectaConfig with segment metadata.

        Returns:
            ResetResult with success status, files written, and any errors.
        """
        start_time = time.time()
        files_written: list[str] = []
        errors: list[str] = []

        try:
            segment_id = config.segment_id

            # Render and write templates
            templates = [
                (segment_path / "skill.md", self._template_renderer.render_skill(config)),
                (
                    segment_path / "_ctx" / f"agent_{segment_id}.md",
                    self._template_renderer.render_agent(config),
                ),
                (
                    segment_path / "_ctx" / f"prime_{segment_id}.md",
                    self._template_renderer.render_prime(config, []),
                ),
                (
                    segment_path / "_ctx" / f"session_{segment_id}.md",
                    self._template_renderer.render_session(config),
                ),
                (
                    segment_path / "readme_tf.md",
                    self._template_renderer.render_readme(config),
                ),
            ]

            for file_path, content in templates:
                try:
                    # Ensure parent directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
                    files_written.append(str(file_path))
                except Exception as e:
                    errors.append(f"Failed to write {file_path}: {e}")

            if errors:
                return ResetResult(
                    success=False,
                    files_written=files_written,
                    errors=errors,
                    validation_passed=False,
                )

            # Run build
            self._build_use_case.execute(segment_path)

            # Run validation
            result = self._validate_use_case.execute(segment_path)
            validation_passed = result.passed

            self._telemetry.observe("ctx.reset", int((time.time() - start_time) * 1000))

            return ResetResult(
                success=validation_passed,
                files_written=files_written,
                errors=errors if not validation_passed else [],
                validation_passed=validation_passed,
            )

        except Exception as e:
            self._telemetry.event(
                "ctx.reset", {}, {"status": "error"}, int((time.time() - start_time) * 1000)
            )
            errors.append(str(e))
            return ResetResult(
                success=False,
                files_written=files_written,
                errors=errors,
                validation_passed=False,
            )
