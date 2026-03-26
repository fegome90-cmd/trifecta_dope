from src.infrastructure.daemon.protocol import (
    MAX_REQUEST_SIZE,
    ReadResult,
    build_health_payload,
    build_json_response,
    build_request_too_large_response,
    build_text_response,
    decode_request,
    parse_request,
    read_request,
)


class FakeConnection:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def recv(self, size: int) -> bytes:
        if not self._payload:
            return b""
        chunk = self._payload[:size]
        self._payload = self._payload[size:]
        return chunk


def test_parse_request_text_command() -> None:
    assert parse_request("PING") == {"kind": "text", "command": "PING"}


def test_parse_request_json_envelope() -> None:
    parsed = parse_request('{"method":"textDocument/definition","params":{}}')

    assert parsed["kind"] == "json"
    assert parsed["payload"] == {"method": "textDocument/definition", "params": {}}


def test_decode_request_replaces_invalid_utf8() -> None:
    assert decode_request(b"PING\xff") == "PING�"


def test_build_request_too_large_response_golden() -> None:
    assert build_request_too_large_response() == (
        b'{"status": "error", "message": "Request too large (max 16KB)"}\n'
    )


def test_build_text_response_golden() -> None:
    assert build_text_response("ERROR: Timeout") == b"ERROR: Timeout\n"


def test_build_json_response_golden() -> None:
    payload = {"status": "ok", "pid": 42}

    assert build_json_response(payload) == b'{"status": "ok", "pid": 42}\n'


def test_build_health_payload_shape() -> None:
    payload = build_health_payload(pid=42, uptime=3, lsp_state="READY", lsp_enabled=True)

    assert list(payload.keys()) == ["status", "pid", "uptime", "version", "protocol", "lsp"]
    assert payload == {
        "status": "ok",
        "pid": 42,
        "uptime": 3,
        "version": "1.0.0",
        "protocol": ["PING", "HEALTH", "SHUTDOWN"],
        "lsp": {"state": "READY", "enabled": True},
    }


def test_parse_request_empty() -> None:
    assert parse_request("") == {"kind": "empty"}


def test_request_size_constant_frozen() -> None:
    assert MAX_REQUEST_SIZE == 16_384


def test_read_request_accepts_exact_limit_with_eof() -> None:
    conn = FakeConnection(b"x" * MAX_REQUEST_SIZE)

    assert read_request(conn, MAX_REQUEST_SIZE) == ReadResult(raw_data=b"x" * MAX_REQUEST_SIZE)


def test_read_request_detects_oversized_multi_chunk() -> None:
    conn = FakeConnection(b"x" * (MAX_REQUEST_SIZE + 1))

    assert read_request(conn, MAX_REQUEST_SIZE) == ReadResult(
        raw_data=b"x" * MAX_REQUEST_SIZE,
        oversized=True,
    )


def test_read_request_stops_at_newline_before_limit() -> None:
    conn = FakeConnection(b"PING\nTRAILING")

    assert read_request(conn, MAX_REQUEST_SIZE) == ReadResult(raw_data=b"PING\n")
