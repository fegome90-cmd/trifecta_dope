from __future__ import annotations

import json
import os
import sys
from typing import Any


REQUIRED_TOOLS = [
    "create_issue",
    "update_issue",
    "get_issue",
    "list_issues",
    "add_comment",
    "set_labels",
    "transition_issue_state",
    "resolve_team",
    "list_workflow_states",
]


class FakeLinearMCP:
    def __init__(self) -> None:
        self.team_id = os.environ.get("LINEAR_FAKE_TEAM_ID", "team-123")
        self.missing_cap = {
            x.strip() for x in os.environ.get("LINEAR_FAKE_MISSING_CAPABILITY", "").split(",") if x.strip()
        }
        self.rate_limit_tool = os.environ.get("LINEAR_FAKE_RATE_LIMIT_TOOL", "")
        self.rate_limit_count = int(os.environ.get("LINEAR_FAKE_RATE_LIMIT_COUNT", "0"))
        self.rate_limit_seen = 0
        self.workflow_variant = os.environ.get("LINEAR_FAKE_WORKFLOW_VARIANT", "default")
        self.db_path = os.environ.get("LINEAR_FAKE_DB", "").strip()

        self.issues: dict[str, dict[str, Any]] = {}
        self.issue_by_wo: dict[str, str] = {}
        self.next_id = 1
        self._load_db()

    def _load_db(self) -> None:
        if not self.db_path:
            return
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.issues = data.get("issues", {})
            self.issue_by_wo = data.get("issue_by_wo", {})
            self.next_id = int(data.get("next_id", 1))
        except Exception:
            self.issues = {}
            self.issue_by_wo = {}
            self.next_id = 1

    def _save_db(self) -> None:
        if not self.db_path:
            return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "issues": self.issues,
                    "issue_by_wo": self.issue_by_wo,
                    "next_id": self.next_id,
                },
                f,
                sort_keys=True,
            )

    def _tool_list(self) -> list[dict[str, str]]:
        tools = [name for name in REQUIRED_TOOLS if name not in self.missing_cap]
        return [{"name": name} for name in tools]

    def _states(self) -> list[dict[str, str]]:
        if self.workflow_variant == "missing_done":
            return [
                {"id": "st-backlog", "name": "Todo"},
                {"id": "st-progress", "name": "In Progress"},
                {"id": "st-cancel", "name": "Canceled"},
            ]
        return [
            {"id": "st-backlog", "name": "Todo"},
            {"id": "st-progress", "name": "In Progress"},
            {"id": "st-done", "name": "Done"},
            {"id": "st-cancel", "name": "Canceled"},
        ]

    def _maybe_rate_limit(self, tool_name: str) -> dict[str, Any] | None:
        if tool_name != self.rate_limit_tool:
            return None
        if self.rate_limit_seen >= self.rate_limit_count:
            return None
        self.rate_limit_seen += 1
        return {
            "code": "RATE_LIMITED",
            "message": "rate limited",
            "data": {"retry_ms": 50},
        }

    def handle_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        rate_limit = self._maybe_rate_limit(name)
        if rate_limit is not None:
            raise RuntimeError(json.dumps(rate_limit))

        if name == "resolve_team":
            return {"team_id": self.team_id, "team_key": arguments.get("team_key", "")}
        if name == "list_workflow_states":
            return {"states": self._states()}
        if name == "create_issue":
            wo_id = str(arguments.get("wo_id") or "")
            if wo_id and wo_id in self.issue_by_wo:
                issue_id = self.issue_by_wo[wo_id]
                return {"issue": self.issues[issue_id], "created": False}
            issue_id = f"LIN-{self.next_id}"
            self.next_id += 1
            issue = {
                "id": issue_id,
                "wo_id": wo_id,
                "title": arguments.get("title", ""),
                "description": arguments.get("description", ""),
                "priority": arguments.get("priority", "medium"),
                "labels": list(arguments.get("labels", [])),
                "assignee": arguments.get("assignee"),
                "state": arguments.get("state"),
            }
            self.issues[issue_id] = issue
            if wo_id:
                self.issue_by_wo[wo_id] = issue_id
            self._save_db()
            return {"issue": issue, "created": True}
        if name == "update_issue":
            issue_id = str(arguments.get("issue_id") or "")
            if issue_id not in self.issues:
                return {"updated": False}
            issue = self.issues[issue_id]
            for key in ["title", "description", "priority", "assignee", "state"]:
                if key in arguments:
                    issue[key] = arguments[key]
            if "labels" in arguments:
                issue["labels"] = list(arguments["labels"])
            self._save_db()
            return {"issue": issue, "updated": True}
        if name == "get_issue":
            issue_id = str(arguments.get("issue_id") or "")
            return {"issue": self.issues.get(issue_id)}
        if name == "list_issues":
            return {"issues": list(self.issues.values())}
        if name == "add_comment":
            issue_id = str(arguments.get("issue_id") or "")
            body = str(arguments.get("body") or "")
            issue = self.issues.get(issue_id)
            if issue is None:
                return {"ok": False}
            issue.setdefault("comments", []).append(body)
            self._save_db()
            return {"ok": True}
        if name == "set_labels":
            issue_id = str(arguments.get("issue_id") or "")
            issue = self.issues.get(issue_id)
            if issue is None:
                return {"ok": False}
            issue["labels"] = list(arguments.get("labels", []))
            self._save_db()
            return {"ok": True}
        if name == "transition_issue_state":
            issue_id = str(arguments.get("issue_id") or "")
            state_id = str(arguments.get("state_id") or "")
            issue = self.issues.get(issue_id)
            if issue is None:
                return {"ok": False}
            issue["state"] = state_id
            self._save_db()
            return {"ok": True}

        return {"ok": False}


def main() -> None:
    fake = FakeLinearMCP()
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        if method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": fake._tool_list()},
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments") or {}
            try:
                result = fake.handle_tool(tool_name, args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result,
                }
            except RuntimeError as exc:
                err = json.loads(str(exc))
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": err,
                }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        resp = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": "METHOD_NOT_FOUND", "message": method},
        }
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
