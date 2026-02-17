#!/usr/bin/env python3
"""Bridge stdio JSON-RPC MCP client calls to Codex Linear streamable HTTP MCP."""

from __future__ import annotations

import json
import os
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROTO_VERSION = "2024-11-05"
DEFAULT_CODEX_CONFIG = Path.home() / ".codex" / "config.toml"


class BridgeError(RuntimeError):
    pass


def _load_linear_config() -> tuple[str, str]:
    # Explicit env overrides take precedence.
    env_url = os.environ.get("LINEAR_MCP_URL", "").strip()
    env_token = os.environ.get("LINEAR_MCP_BEARER_TOKEN", "").strip()
    if env_url and env_token:
        return env_url, env_token

    cfg_path = Path(os.environ.get("CODEX_CONFIG_PATH", str(DEFAULT_CODEX_CONFIG)))
    if not cfg_path.exists():
        raise BridgeError(f"Codex config not found: {cfg_path}")

    parsed = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    linear = (parsed.get("mcp_servers") or {}).get("linear") or {}
    url = str(linear.get("url") or env_url).strip()
    raw = str(linear.get("bearer_token_env_var") or "").strip()
    if not url:
        raise BridgeError("Missing linear MCP URL (set LINEAR_MCP_URL or Codex config mcp_servers.linear.url)")

    # Note: Codex config key is named bearer_token_env_var; support env-var name and raw token forms.
    token = env_token
    if not token and raw:
        token = os.environ.get(raw, "") if raw.isupper() else raw
    if not token:
        raise BridgeError(
            "Missing Linear MCP bearer token "
            "(set LINEAR_MCP_BEARER_TOKEN or configure mcp_servers.linear.bearer_token_env_var)"
        )

    return url, token


def _open_with_auth(
    url: str,
    token: str,
    payload: dict[str, Any],
    session_id: str | None,
    auth_value: str,
):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": auth_value,
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=20)  # nosec B310 - controlled URL from trusted config/env


def _post_sse_json(url: str, token: str, payload: dict[str, Any], session_id: str | None) -> tuple[dict[str, Any], str | None]:
    auth_candidates = [f"Bearer {token}", token]
    last_exc: Exception | None = None
    for auth_value in auth_candidates:
        try:
            with _open_with_auth(url, token, payload, session_id, auth_value) as resp:
                new_session = resp.headers.get("mcp-session-id") or session_id
                content_type = str(resp.headers.get("content-type") or "").lower()
                if "text/event-stream" in content_type:
                    # Streamable HTTP: consume the first JSON event and return immediately.
                    while True:
                        line = resp.readline()
                        if not line:
                            break
                        text = line.decode("utf-8", errors="replace").strip()
                        if not text.startswith("data: "):
                            continue
                        candidate = text[6:].strip()
                        if not candidate:
                            continue
                        return json.loads(candidate), new_session
                    return {}, new_session

                raw = resp.read().decode("utf-8", errors="replace")
                if not raw.strip():
                    return {}, new_session
                return json.loads(raw), new_session
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            # Linear GraphQL-style guidance: retry without Bearer once.
            if auth_value.startswith("Bearer ") and "Remove the Bearer prefix" in detail:
                last_exc = exc
                continue
            raise BridgeError(f"HTTP Error {exc.code}: {detail}") from exc
    if last_exc:
        raise last_exc
    raise BridgeError("Unable to authenticate against Linear MCP endpoint")


def main() -> int:
    try:
        url, token = _load_linear_config()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": "CONFIG_ERROR", "message": str(exc)},
                }
            ),
            flush=True,
        )
        return 1

    session_id: str | None = None
    initialized = False

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": "INVALID_JSON", "message": "invalid JSON request"},
                    }
                ),
                flush=True,
            )
            continue

        req_id = req.get("id")
        method = req.get("method")
        try:
            if method == "tools/list" and not initialized:
                init_req = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTO_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "trifecta-linear-bridge", "version": "0.1.0"},
                    },
                }
                _, session_id = _post_sse_json(url, token, init_req, None)
                initialized = True

            needs_session = method != "initialize"
            out, session_id = _post_sse_json(url, token, req, session_id if needs_session else None)
            if out.get("id") is None and req_id is not None:
                out["id"] = req_id
            if "jsonrpc" not in out:
                out["jsonrpc"] = "2.0"
            print(json.dumps(out, separators=(",", ":")), flush=True)
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": "UPSTREAM_ERROR", "message": str(exc)},
                    }
                ),
                flush=True,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
