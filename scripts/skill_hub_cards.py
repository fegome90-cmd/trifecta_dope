#!/usr/bin/env python3
"""Deprecated shim for the old rival entrypoint.

This file MUST remain a thin delegator to scripts/skill-hub-cards.
It intentionally owns no parsing, classification, or rendering logic.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


HELPER = Path(__file__).resolve().with_name("skill-hub-cards")


def main() -> int:
    print(
        "skill_hub_cards.py is deprecated; delegating to skill-hub-cards.",
        file=sys.stderr,
    )
    argv = [sys.executable, str(HELPER), "--stdin-search-output", *sys.argv[1:]]
    try:
        os.execv(sys.executable, argv)
    except OSError as exc:
        print(f"skill_hub_cards.py failed to exec delegated helper: {exc}", file=sys.stderr)
        raise SystemExit(127) from exc


if __name__ == "__main__":
    raise SystemExit(main())
