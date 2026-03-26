import json
import socket
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

MAX_REQUEST_SIZE = 16_384


class ParsedRequest(TypedDict, total=False):
    kind: Literal["empty", "json", "text"]
    payload: dict[str, Any]
    command: str


@dataclass(frozen=True)
class ReadResult:
    raw_data: bytes
    oversized: bool = False


def read_request(conn: socket.socket, max_size: int = MAX_REQUEST_SIZE) -> ReadResult:
    """Read a newline-delimited request with explicit oversized detection.

    Semantics:
    - newline before limit => complete request
    - exact limit + EOF => complete request
    - exact limit + extra byte => oversized request
    """
    raw_data = b""

    while True:
        newline_index = raw_data.find(b"\n")
        if newline_index != -1:
            return ReadResult(raw_data=raw_data[: newline_index + 1], oversized=False)

        if len(raw_data) == max_size:
            extra = conn.recv(1)
            if not extra:
                return ReadResult(raw_data=raw_data, oversized=False)
            return ReadResult(raw_data=raw_data, oversized=True)

        chunk = conn.recv(min(4096, max_size - len(raw_data)))
        if not chunk:
            return ReadResult(raw_data=raw_data, oversized=False)

        raw_data += chunk


def decode_request(raw_data: bytes) -> str:
    return raw_data.decode("utf-8", errors="replace").strip()


def parse_request(data: str) -> ParsedRequest:
    if not data:
        return {"kind": "empty"}

    try:
        req = json.loads(data)
        if isinstance(req, dict) and "method" in req:
            return {"kind": "json", "payload": req}
    except (json.JSONDecodeError, TypeError):
        pass

    return {"kind": "text", "command": data}


def build_json_response(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload).encode() + b"\n"


def build_text_response(message: str) -> bytes:
    return f"{message}\n".encode()


def build_health_payload(
    *,
    pid: int,
    uptime: int,
    lsp_state: str,
    lsp_enabled: bool,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "pid": pid,
        "uptime": uptime,
        "version": "1.0.0",
        "protocol": ["PING", "HEALTH", "SHUTDOWN"],
        "lsp": {"state": lsp_state, "enabled": lsp_enabled},
    }


def build_request_too_large_response() -> bytes:
    return build_json_response({"status": "error", "message": "Request too large (max 16KB)"})
