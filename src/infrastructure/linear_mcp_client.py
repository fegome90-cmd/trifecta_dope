from __future__ import annotations

import json
import os
import queue
import random
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any


MAX_MCP_TEXT_BYTES = 256 * 1024

REQUIRED_LINEAR_OPS: dict[str, tuple[str, ...]] = {
    "create_issue": ("create_issue",),
    "update_issue": ("update_issue",),
    "get_issue": ("get_issue",),
    "list_issues": ("list_issues",),
    "add_comment": ("add_comment", "create_comment"),
    "set_labels": ("set_labels", "update_issue"),
    "transition_issue_state": ("transition_issue_state", "update_issue"),
    "resolve_team": ("resolve_team", "list_teams", "get_team"),
    "list_workflow_states": ("list_workflow_states", "list_issue_statuses"),
}


class LinearMCPError(RuntimeError):
    pass


class LinearMCPCapabilityError(LinearMCPError):
    pass


class LinearMCPRateLimitError(LinearMCPError):
    def __init__(self, message: str, retry_ms: int = 0):
        super().__init__(message)
        self.retry_ms = retry_ms


@dataclass
class MCPResponse:
    payload: dict[str, Any]


class LinearMCPClient:
    def __init__(self, command: str | None = None) -> None:
        self.command = command or os.environ.get("LINEAR_MCP_CMD", "").strip()
        if not self.command:
            raise LinearMCPError(
                "LINEAR_MCP_CMD is required (example: 'python -m tests.fixtures.linear_mcp_fake')"
            )
        self.timeout_ms = int(os.environ.get("LINEAR_MCP_TIMEOUT_MS", "5000"))
        self.debug = os.environ.get("LINEAR_MCP_DEBUG", "0") == "1"
        self._request_id = 0
        self._lock = threading.Lock()
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._proc: subprocess.Popen[str] | None = None
        self._reader_thread: threading.Thread | None = None
        self._tool_map: dict[str, str] = {}
        self._tool_names: set[str] = set()

    def _log(self, direction: str, frame: str) -> None:
        if self.debug:
            redacted = frame.replace(os.environ.get("LINEAR_TOKEN", ""), "***")
            sys.stderr.write(f"[linear-mcp:{direction}] {redacted}\n")

    def _ensure_proc(self) -> None:
        if self._proc and self._proc.poll() is None:
            return

        self._proc = subprocess.Popen(
            shlex.split(self.command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        def _reader() -> None:
            assert self._proc is not None and self._proc.stdout is not None
            for raw in self._proc.stdout:
                line = raw.strip()
                if not line:
                    continue
                self._log("in", line)
                try:
                    self._queue.put(json.loads(line))
                except json.JSONDecodeError:
                    self._queue.put({"jsonrpc": "2.0", "id": None, "error": {"code": "INVALID_JSON", "message": line}})

        self._reader_thread = threading.Thread(target=_reader, daemon=True)
        self._reader_thread.start()

    def close(self) -> None:
        if not self._proc:
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except OSError:
            pass
        self._proc.terminate()
        self._proc = None

    def __enter__(self) -> "LinearMCPClient":
        self._ensure_proc()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(self, method: str, params: dict[str, Any]) -> MCPResponse:
        # single in-flight request by lock: no pipelining
        with self._lock:
            self._ensure_proc()
            if not self._proc or not self._proc.stdin:
                raise LinearMCPError("MCP process unavailable")

            self._request_id += 1
            req_id = self._request_id
            req = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params,
            }
            line = json.dumps(req, separators=(",", ":"), sort_keys=True)
            self._log("out", line)
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()

            try:
                response = self._queue.get(timeout=self.timeout_ms / 1000)
            except queue.Empty as exc:
                raise LinearMCPError(f"MCP request timeout after {self.timeout_ms}ms ({method})") from exc

            if response.get("id") != req_id:
                raise LinearMCPError(f"MCP protocol mismatch: expected id={req_id}, got={response.get('id')}")

            if "error" in response:
                err = response["error"]
                code = err.get("code", "UNKNOWN")
                msg = err.get("message", "MCP error")
                if code == "RATE_LIMITED":
                    retry_ms = int((err.get("data") or {}).get("retry_ms", 0))
                    raise LinearMCPRateLimitError(msg, retry_ms=retry_ms)
                raise LinearMCPError(f"MCP error {code}: {msg}")

            return MCPResponse(payload=response.get("result", {}))

    def tools_list(self) -> list[dict[str, Any]]:
        result = self._request("tools/list", {}).payload
        tools = result.get("tools", result)
        if not isinstance(tools, list):
            raise LinearMCPError("tools/list returned invalid payload")
        return [t for t in tools if isinstance(t, dict)]

    def check_capabilities(self) -> None:
        names = {t.get("name") for t in self.tools_list() if isinstance(t.get("name"), str)}
        self._tool_names = set(names)
        resolved: dict[str, str] = {}
        missing: list[str] = []
        for op in REQUIRED_LINEAR_OPS:
            selected = self._resolve_capability_tool(op, names)
            if selected:
                resolved[op] = selected
            else:
                missing.append(f"{op}({','.join(REQUIRED_LINEAR_OPS[op])})")
        if missing:
            raise LinearMCPCapabilityError(
                "MCP server missing required operations: " + ", ".join(missing)
            )
        self._tool_map = resolved
        if self.debug:
            self._log("cap", f"capability_map={json.dumps(self._tool_map, sort_keys=True)}")

    @staticmethod
    def _resolve_capability_tool(capability: str, available_tools: set[str]) -> str:
        candidates = REQUIRED_LINEAR_OPS.get(capability, ())
        for tool in candidates:
            if tool in available_tools:
                return tool
        return ""

    def _ensure_capabilities(self) -> None:
        if not self._tool_map:
            self.check_capabilities()

    def _tool_for(self, op: str) -> str:
        self._ensure_capabilities()
        tool = self._tool_map.get(op, "")
        if not tool:
            raise LinearMCPCapabilityError(f"Missing mapped tool for operation: {op}")
        return tool

    @staticmethod
    def _decode_content_payload(payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("isError") is True:
            content = payload.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") != "text":
                        continue
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        raise LinearMCPError(f"MCP tool error: {text.strip()}")
            raise LinearMCPError("MCP tool returned error content")

        content = payload.get("content")
        if not isinstance(content, list):
            return payload
        saw_text = False
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "text":
                continue
            saw_text = True
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                raise LinearMCPError("MCP content.text is empty or invalid")
            if len(text.encode("utf-8")) > MAX_MCP_TEXT_BYTES:
                raise LinearMCPError(
                    f"MCP content.text exceeds max size ({MAX_MCP_TEXT_BYTES} bytes)"
                )
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                raise LinearMCPError("MCP content.text is not valid JSON")
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"items": parsed}
            raise LinearMCPError("MCP content.text JSON must be object or array")
        if saw_text:
            raise LinearMCPError("MCP content.text could not be decoded")
        raise LinearMCPError("MCP content has no text item")

    @staticmethod
    def _team_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
        teams = payload.get("teams")
        if isinstance(teams, list):
            return [x for x in teams if isinstance(x, dict)]
        items = payload.get("items")
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
        team = payload.get("team")
        if isinstance(team, dict):
            return [team]
        return []

    @staticmethod
    def _status_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
        states = payload.get("states")
        if isinstance(states, list):
            return [x for x in states if isinstance(x, dict)]
        items = payload.get("items")
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
        return []

    def call_tool(self, name: str, arguments: dict[str, Any], retries: int = 3) -> dict[str, Any]:
        for attempt in range(1, retries + 1):
            try:
                res = self._request("tools/call", {"name": name, "arguments": arguments}).payload
                if isinstance(res, dict):
                    return self._decode_content_payload(res)
                return {"value": res}
            except LinearMCPRateLimitError as exc:
                if attempt >= retries:
                    raise
                base = exc.retry_ms / 1000 if exc.retry_ms > 0 else 0.2 * attempt
                time.sleep(base + random.uniform(0, 0.05))
        raise LinearMCPError("unreachable")

    def resolve_team(self, team_key: str) -> dict[str, Any]:
        tool = self._tool_for("resolve_team")
        if tool == "resolve_team":
            return self.call_tool("resolve_team", {"team_key": team_key})
        if tool == "get_team":
            raw = self._decode_content_payload(self.call_tool("get_team", {"query": team_key}))
            teams = self._team_candidates(raw)
        else:
            raw = self._decode_content_payload(self.call_tool("list_teams", {"query": team_key, "limit": 50}))
            teams = self._team_candidates(raw)
            if not teams:
                raw = self._decode_content_payload(self.call_tool("list_teams", {"limit": 250}))
                teams = self._team_candidates(raw)

        if not teams:
            raise LinearMCPError(f"Unable to resolve team from MCP response for key '{team_key}'")
        needle = team_key.strip().lower()
        if not needle:
            raise LinearMCPError("Team key is empty; cannot resolve team")
        exact = []
        for team in teams:
            tid = str(team.get("id") or "").strip().lower()
            tkey = str(team.get("key") or "").strip().lower()
            tname = str(team.get("name") or "").strip().lower()
            if needle in {tid, tkey, tname}:
                exact.append(team)

        if len(exact) == 1:
            team = exact[0]
        elif len(exact) > 1:
            raise LinearMCPError(f"Ambiguous team_key '{team_key}' matches multiple teams")
        else:
            raise LinearMCPError(f"No team matched team_key '{team_key}'")

        team_id = str(team.get("id") or "").strip()
        if not team_id:
            raise LinearMCPError(f"Resolved team missing id for key '{team_key}'")
        return {
            "team_id": team_id,
            "team_key": str(team.get("key") or team_key),
            "team_name": str(team.get("name") or ""),
        }

    def list_workflow_states(self, team_id: str) -> dict[str, Any]:
        tool = self._tool_for("list_workflow_states")
        if tool == "list_workflow_states":
            return self.call_tool("list_workflow_states", {"team_id": team_id})
        raw = self._decode_content_payload(self.call_tool("list_issue_statuses", {"team": team_id}))
        statuses = self._status_candidates(raw)
        return {"states": statuses}

    def create_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "title",
            "description",
            "team",
            "cycle",
            "milestone",
            "priority",
            "project",
            "state",
            "assignee",
            "delegate",
            "labels",
            "dueDate",
            "parentId",
            "estimate",
            "links",
            "blocks",
            "blockedBy",
            "relatedTo",
            "duplicateOf",
        }
        args = {k: v for k, v in payload.items() if k in allowed}
        return self.call_tool("create_issue", args)

    def update_issue(self, issue_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "title",
            "description",
            "team",
            "milestone",
            "priority",
            "project",
            "state",
            "cycle",
            "assignee",
            "delegate",
            "labels",
            "parentId",
            "dueDate",
            "estimate",
            "links",
            "blocks",
            "blockedBy",
            "relatedTo",
            "duplicateOf",
        }
        args = {"id": issue_id, **{k: v for k, v in payload.items() if k in allowed}}
        res = self.call_tool("update_issue", args)
        if res.get("updated") is False and "set_labels" in self._tool_names:
            # Legacy adapter compatibility path (fake MCP fixture).
            return self.call_tool("update_issue", {"issue_id": issue_id, **payload})
        return res

    def get_issue(self, issue_id: str) -> dict[str, Any]:
        res = self.call_tool("get_issue", {"id": issue_id})
        if res.get("issue") is None and "set_labels" in self._tool_names:
            return self.call_tool("get_issue", {"issue_id": issue_id})
        if "issue" in res:
            return res
        if isinstance(res.get("id"), str):
            return {"issue": res}
        return res

    def list_issues(self, team_id: str) -> dict[str, Any]:
        res = self.call_tool("list_issues", {"team": team_id})
        if "issues" in res:
            return res
        items = res.get("items")
        if isinstance(items, list):
            return {"issues": items}
        return res

    def add_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        tool = self._tool_for("add_comment")
        if tool == "add_comment":
            return self.call_tool("add_comment", {"issue_id": issue_id, "body": body})
        return self.call_tool("create_comment", {"issueId": issue_id, "body": body})

    def set_labels(self, issue_id: str, labels: list[str]) -> dict[str, Any]:
        tool = self._tool_for("set_labels")
        if tool == "set_labels":
            return self.call_tool("set_labels", {"issue_id": issue_id, "labels": labels})
        return self.call_tool("update_issue", {"id": issue_id, "labels": labels})

    def transition_issue_state(self, issue_id: str, state_id: str) -> dict[str, Any]:
        tool = self._tool_for("transition_issue_state")
        if tool == "transition_issue_state":
            return self.call_tool("transition_issue_state", {"issue_id": issue_id, "state_id": state_id})
        return self.call_tool("update_issue", {"id": issue_id, "state": state_id})
