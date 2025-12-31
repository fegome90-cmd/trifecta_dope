```python
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import yaml


@dataclass(frozen=True)
class Block:
    kind: str  # heading | paragraph | fence
    text: str
    heading_level: Optional[int] = None
    heading_text: Optional[str] = None


@dataclass(frozen=True)
class ChunkRules:
    chunk_size: int
    section_max_chars: int
    overlap_pct: float


@dataclass(frozen=True)
class Chunk:
    text: str
    source_path: str
    title_path: List[str]
    char_count: int
    chunk_hash: str
    doc: str


def normalize_markdown(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                text = "\n".join(lines[i + 1 :])
                break
    return text.strip() + "\n"


def parse_markdown(md: str) -> List[Block]:
    blocks: List[Block] = []
    buf: List[str] = []
    in_fence = False
    fence_marker: Optional[str] = None

    def flush_paragraph() -> None:
        nonlocal buf
        if buf:
            blocks.append(Block(kind="paragraph", text="".join(buf)))
            buf = []

    for line
