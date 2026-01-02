"""Deprecated code path tracking utilities.

Emits telemetry events when deprecated code paths are used.
Policy controlled by TRIFECTA_DEPRECATED env var (off|warn|fail).
"""

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.telemetry import Telemetry


def maybe_emit_deprecated(
    deprecated_id: str,
    telemetry: "Telemetry",
) -> None:
    """Emit deprecated usage event based on policy.

    Args:
        deprecated_id: Stable identifier from docs/deprecations.yaml
        telemetry: Existing telemetry instance (reuses current writer)

    Raises:
        SystemExit: If policy is 'fail', exits with code 2

    Policy (TRIFECTA_DEPRECATED env var):
        - off: no tracking (default)
        - warn: emit telemetry event only
        - fail: emit event + force exit code 2 (for CI/harness)
    """
    policy = os.getenv("TRIFECTA_DEPRECATED", "off")

    if policy == "off":
        return

    # Emit event via existing telemetry (no new log files)
    telemetry.event(
        "deprecated.used",
        {"id": deprecated_id},
        {},
        0,  # No timing for deprecation events
    )

    if policy == "fail":
        # Force failure for CI/harness detection
        print(f"TRIFECTA_DEPRECATED=fail: {deprecated_id}", file=sys.stderr)
        raise SystemExit(2)
