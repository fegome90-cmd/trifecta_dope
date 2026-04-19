"""
Error Card utilities for structured CLI error output.

Provides fail-closed error messages with stable markers for testing.

Reference-only note:
- Promoted runtime authority for skill-hub error framing lives in /scripts.
"""

from __future__ import annotations

import sys
from typing import IO


def render_error_card(
    *,
    error_code: str,
    error_class: str,
    cause: str,
    next_steps: list[str],
    verify_cmd: str,
) -> str:
    """Render a structured error card with stable markers.

    Markers included for grep/assertion:
    - TRIFECTA_ERROR_CODE: <code>
    - CLASS: <class>
    - NEXT_STEPS:
    - VERIFY:
    """
    steps = "\n  ".join(next_steps)
    return (
        f"TRIFECTA_ERROR_CODE: {error_code}\n"
        f"❌ TRIFECTA_ERROR: {error_code}\n"
        f"CLASS: {error_class}\n"
        f"CAUSE: {cause}\n\n"
        f"NEXT_STEPS:\n"
        f"  {steps}\n\n"
        f"VERIFY:\n"
        f"  {verify_cmd}\n"
    )


def emit_skill_hub_error_card(
    *,
    error_code: str,
    error_class: str,
    cause: str,
    next_steps: list[str],
    verify_cmd: str,
    file: IO[str] | None = None,
) -> None:
    """Write a structured skill-hub error card to stderr by default."""
    output = file or sys.stderr
    print(
        render_error_card(
            error_code=error_code,
            error_class=error_class,
            cause=cause,
            next_steps=next_steps,
            verify_cmd=verify_cmd,
        ),
        file=output,
        end="",
    )
