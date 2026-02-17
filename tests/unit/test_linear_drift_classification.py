from src.application.linear_reconcile import classify_drift
from src.domain.linear_models import LinearPolicy


def _policy() -> LinearPolicy:
    return LinearPolicy(
        mode="viewer",
        direction="outbound",
        policy_version="v1",
        team_key="TRI",
        team_id="team-123",
        outbound_allow=("title", "description", "priority", "labels", "assignee", "state", "comments"),
        inbound_allow=(),
        drift_severity={
            "INFO": ("description", "labels"),
            "WARN": ("priority", "assignee"),
            "FATAL": ("status_critical", "dod", "verify", "execution", "evidence"),
        },
        status_map={"pending": None, "running": None, "partial": None, "done": None, "failed": None},
    )


def test_classify_info() -> None:
    assert classify_drift({"description"}, _policy()) == "INFO"


def test_classify_warn() -> None:
    assert classify_drift({"priority"}, _policy()) == "WARN"


def test_classify_fatal_for_state() -> None:
    assert classify_drift({"state"}, _policy()) == "FATAL"
