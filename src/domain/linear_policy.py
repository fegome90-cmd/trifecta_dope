from pathlib import Path

import yaml

from src.domain.linear_models import LinearPolicy, REQUIRED_DRIFT_LEVELS, REQUIRED_TRIFECTA_STATUSES


class LinearPolicyError(ValueError):
    pass


_REQUIRED_KEYS = {
    "mode",
    "direction",
    "policy_version",
    "outbound_allow",
    "inbound_allow",
    "drift_severity",
    "status_map",
}


def _must_have_keys(data: dict) -> None:
    for key in sorted(_REQUIRED_KEYS):
        if key not in data:
            raise LinearPolicyError(f"missing required key: {key}")


def _validate_mode_and_direction(data: dict) -> None:
    if data.get("mode") != "viewer":
        raise LinearPolicyError("mode must be 'viewer'")
    if data.get("direction") != "outbound":
        raise LinearPolicyError("direction must be 'outbound'")


def _validate_teams(data: dict) -> tuple[str, str]:
    team_key = str(data.get("team_key") or "").strip()
    team_id = str(data.get("team_id") or "").strip()
    if not team_key and not team_id:
        raise LinearPolicyError("team_key or team_id is required")
    return team_key, team_id


def _validate_allowlists(data: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    outbound_allow = data.get("outbound_allow")
    inbound_allow = data.get("inbound_allow")
    if not isinstance(outbound_allow, list) or not all(isinstance(x, str) for x in outbound_allow):
        raise LinearPolicyError("outbound_allow must be a list of strings")
    if not isinstance(inbound_allow, list) or not all(isinstance(x, str) for x in inbound_allow):
        raise LinearPolicyError("inbound_allow must be a list of strings")
    if inbound_allow:
        raise LinearPolicyError("inbound_allow must be empty in viewer mode")
    return tuple(outbound_allow), tuple(inbound_allow)


def _validate_drift_severity(data: dict) -> dict[str, tuple[str, ...]]:
    value = data.get("drift_severity")
    if not isinstance(value, dict):
        raise LinearPolicyError("drift_severity must be a mapping")

    resolved: dict[str, tuple[str, ...]] = {}
    for level in REQUIRED_DRIFT_LEVELS:
        fields = value.get(level)
        if not isinstance(fields, list) or not all(isinstance(x, str) for x in fields):
            raise LinearPolicyError(f"drift_severity.{level} must be a list of strings")
        resolved[level] = tuple(fields)
    return resolved


def _validate_status_map(data: dict) -> dict[str, str | None]:
    value = data.get("status_map")
    if not isinstance(value, dict):
        raise LinearPolicyError("status_map must be a mapping")
    resolved: dict[str, str | None] = {}
    for status in REQUIRED_TRIFECTA_STATUSES:
        if status not in value:
            raise LinearPolicyError(f"status_map missing key: {status}")
        state_id = value[status]
        if state_id is not None and not isinstance(state_id, str):
            raise LinearPolicyError(f"status_map.{status} must be string or null")
        resolved[status] = state_id
    return resolved


def load_linear_policy(path: Path) -> LinearPolicy:
    if not path.exists():
        raise LinearPolicyError(f"policy file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise LinearPolicyError(f"invalid YAML policy: {exc}") from exc

    if not isinstance(raw, dict):
        raise LinearPolicyError("policy root must be a mapping")

    _must_have_keys(raw)
    _validate_mode_and_direction(raw)
    team_key, team_id = _validate_teams(raw)
    outbound_allow, inbound_allow = _validate_allowlists(raw)
    drift_severity = _validate_drift_severity(raw)
    status_map = _validate_status_map(raw)

    policy_version = str(raw.get("policy_version") or "").strip()
    if not policy_version:
        raise LinearPolicyError("policy_version must be non-empty")
    project = str(raw.get("project") or "").strip()

    return LinearPolicy(
        mode="viewer",
        direction="outbound",
        policy_version=policy_version,
        team_key=team_key,
        team_id=team_id,
        outbound_allow=outbound_allow,
        inbound_allow=inbound_allow,
        drift_severity=drift_severity,
        status_map=status_map,
        project=project,
    )
