from dataclasses import dataclass
from typing import Literal


REQUIRED_TRIFECTA_STATUSES = ("pending", "running", "partial", "done", "failed")
REQUIRED_DRIFT_LEVELS = ("INFO", "WARN", "FATAL")

DriftLevel = Literal["INFO", "WARN", "FATAL"]


@dataclass(frozen=True)
class LinearPolicy:
    mode: str
    direction: str
    policy_version: str
    team_key: str
    team_id: str
    outbound_allow: tuple[str, ...]
    inbound_allow: tuple[str, ...]
    drift_severity: dict[str, tuple[str, ...]]
    status_map: dict[str, str | None]
    project: str = ""


@dataclass(frozen=True)
class ProjectionResult:
    wo_id: str
    payload: dict
    fingerprint: str


@dataclass(frozen=True)
class DriftFinding:
    wo_id: str
    changed_fields: tuple[str, ...]
    severity: DriftLevel
    linear_issue_id: str
