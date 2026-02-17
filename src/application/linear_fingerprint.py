import hashlib
import json
from typing import Any


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_projection_fingerprint(payload: dict[str, Any], policy_version: str) -> str:
    canonical = _canonical_json(payload)
    raw = f"{canonical}|{policy_version}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
