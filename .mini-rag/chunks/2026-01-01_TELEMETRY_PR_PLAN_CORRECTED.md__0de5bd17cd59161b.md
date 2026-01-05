```python
"""Unit tests for telemetry extension (PR#1)."""

import json
import time
from pathlib import Path
import pytest
from src.infrastructure.telemetry import Telemetry, RESERVED_KEYS, _relpath


class TestReservedKeyProtection:
    """Test reserved key collision detection."""

    def test_collision_raises_error(self, tmp_path):
        """Verify ValueError on reserved key collision."""
        telemetry = Telemetry(tmp_path, level="lite")

        with pytest.raises(ValueError, match="reserved keys"):
            telemetry.event(
                "test.cmd",
                {},
                {},
                100,
                ts="2026-01-01T00:00:00Z",  # RESERVED KEY
            )

    def test_multiple_collisions(self, tmp_path):
        """Verify error message includes all colliding keys."""
        telemetry = Telemetry(tmp_path, level="lite")

        with pytest.raises(ValueError, match="ts.*run_id"):
            telemetry.event(
                "test.cmd",
                {},
                {},
                100,
                ts="2026-01-01",
                run_id="fake_id",
            )

    def test_safe_extra_fields(self, tmp_path):
        """Verify non-reserved keys accepted."""
        telemetry = Telemetry(tmp_path, level="lite")

        # Should not raise
        telemetry.event(
            "test.cmd",
            {},
            {},
