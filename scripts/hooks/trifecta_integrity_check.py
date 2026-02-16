#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

WO_RE = re.compile(r"^WO-\d+\.ya?ml$")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    root = Path(os.popen("git rev-parse --show-toplevel").read().strip())
    ctx = root / "_ctx" / "jobs"
    if not ctx.exists():
        fail("_ctx/jobs not found")

    states = ["pending", "running", "done", "failed"]
    seen: dict[str, list[str]] = {}

    for st in states:
        d = ctx / st
        if not d.exists():
            continue
        for p in d.iterdir():
            if p.is_file() and WO_RE.match(p.name):
                seen.setdefault(p.stem, []).append(st)

    multi = {k: v for k, v in seen.items() if len(v) > 1}
    if multi:
        fail(f"WOs present in multiple states: {multi}")

    running_dir = ctx / "running"
    if running_dir.exists():
        for p in running_dir.iterdir():
            if p.is_file() and WO_RE.match(p.name):
                lock = running_dir / f"{p.stem}.lock"
                if not lock.exists():
                    fail(f"Missing lock for running WO: {p.name}")

    print("OK: trifecta integrity check PASS")


if __name__ == "__main__":
    main()
