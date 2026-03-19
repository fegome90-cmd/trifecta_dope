"""Segment indexing policy domain model.

SSOT: Policy is defined ONLY in trifecta_config.json → indexing_policy field.
Default: GENERIC if no policy specified.

Author: Trifecta Team
Date: 2026-03-19
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class SegmentIndexingPolicy(str, Enum):
    """
    Policy for how a segment should be indexed.

    GENERIC (default): Standard indexing behavior, no manifest-driven typing.
    SKILL_HUB: Manifest-driven indexing, only entries in manifest are discoverable.
    """

    GENERIC = "generic"
    SKILL_HUB = "skill_hub"

    @classmethod
    def detect(cls, segment_path: Path) -> "SegmentIndexingPolicy":
        """
        Detect the indexing policy for a segment.

        SSOT: trifecta_config.json → indexing_policy field
        Default: GENERIC

        Args:
            segment_path: Path to the segment root directory.

        Returns:
            The detected policy (GENERIC or SKILL_HUB).
        """
        config_path = segment_path / "_ctx" / "trifecta_config.json"

        if not config_path.exists():
            logger.debug(f"No config found at {config_path}, defaulting to GENERIC")
            return cls.GENERIC

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            policy_value = data.get("indexing_policy", cls.GENERIC.value)

            if policy_value == cls.SKILL_HUB.value:
                return cls.SKILL_HUB

            return cls.GENERIC

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to parse config at {config_path}: {e}, defaulting to GENERIC")
            return cls.GENERIC
