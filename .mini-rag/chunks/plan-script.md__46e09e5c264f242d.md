#!/usr/bin/env python3
import hashlib, json, re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalize(md: str) -> str:
    md = md.replace("\r\n", "\n").strip()
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md + "\n"

def chunk_by_headings(doc_id: str, md: str, max_chars: int = 6000):
    lines = md.splitlines()
    sections = []
    title, level, buf = "INTRO", 0, []

    def flush():
        nonlocal title, level, buf
        if buf:
            sections.append((title, level, "\n".join(buf).strip()))
            buf = []

    for ln in lines:
        m = HEADING_RE.match(ln)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            buf.append(ln)
        else:
            buf.append(ln)
    flush()

    chunks = []
    i = 0
    for t, lvl, txt in sections:
        if not txt:
            continue
