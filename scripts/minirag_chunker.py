from __future__ import annotations

import argparse
import fnmatch
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
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                normalized = "\n".join(lines[i + 1 :])
                break
    return normalized.strip() + "\n"


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

    for line in md.splitlines(keepends=True):
        stripped = line.lstrip()
        is_fence = stripped.startswith("```") or stripped.startswith("~~~")
        if is_fence:
            marker = stripped[:3]
            if not in_fence:
                flush_paragraph()
                in_fence = True
                fence_marker = marker
                buf = [line]
                continue
            if fence_marker is None or marker == fence_marker:
                buf.append(line)
                blocks.append(Block(kind="fence", text="".join(buf)))
                buf = []
                in_fence = False
                fence_marker = None
                continue

        if in_fence:
            buf.append(line)
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level_marker = stripped.split(" ", 1)[0]
            level = len(level_marker)
            heading_text = stripped[len(level_marker) :].strip()
            blocks.append(
                Block(kind="heading", text=line, heading_level=level, heading_text=heading_text)
            )
            continue

        if stripped.strip() == "":
            buf.append(line)
            flush_paragraph()
            continue

        buf.append(line)

    flush_paragraph()
    return blocks


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _split_paragraphs(blocks: Sequence[Block]) -> List[str]:
    return [block.text for block in blocks]


def chunk_blocks(blocks: Sequence[Block], rules: ChunkRules, source_path: str) -> List[Chunk]:
    chunks: List[Chunk] = []
    seen_hashes: set[str] = set()
    title_path: List[str] = []
    section_blocks: List[Block] = []

    def flush_section() -> None:
        nonlocal section_blocks
        if not section_blocks:
            return
        section_text = "".join(b.text for b in section_blocks)
        if len(section_text) <= rules.section_max_chars:
            _append_chunk(section_text)
        else:
            _append_fallback(section_blocks)
        section_blocks = []

    def _append_chunk(text: str) -> None:
        normalized = text.strip() + "\n"
        chunk_hash = _hash_text(normalized)
        if chunk_hash in seen_hashes:
            return
        seen_hashes.add(chunk_hash)
        doc = os.path.basename(source_path)
        chunks.append(
            Chunk(
                text=normalized,
                source_path=source_path,
                title_path=list(title_path),
                char_count=len(normalized),
                chunk_hash=chunk_hash,
                doc=doc,
            )
        )

    def _append_fallback(section: Sequence[Block]) -> None:
        paragraphs = _split_paragraphs(section)
        buffer: List[str] = []
        buffer_len = 0
        for para in paragraphs:
            if len(para) > rules.chunk_size:
                if buffer:
                    _append_chunk("".join(buffer))
                    buffer = []
                    buffer_len = 0
                _split_large_paragraph(para)
                continue
            if buffer_len + len(para) > rules.chunk_size and buffer:
                _append_chunk("".join(buffer))
                buffer = []
                buffer_len = 0
            buffer.append(para)
            buffer_len += len(para)
        if buffer:
            _append_chunk("".join(buffer))

    def _split_large_paragraph(text: str) -> None:
        overlap = max(1, int(rules.chunk_size * min(rules.overlap_pct, 0.05)))
        step = max(1, rules.chunk_size - overlap)
        start = 0
        while start < len(text):
            end = min(start + rules.chunk_size, len(text))
            _append_chunk(text[start:end])
            if end >= len(text):
                break
            start += step

    for block in blocks:
        if block.kind == "heading" and block.heading_level is not None:
            flush_section()
            level = min(block.heading_level, 3)
            title_path = title_path[: level - 1]
            title_path.append(block.heading_text or "")
            section_blocks.append(block)
            continue
        section_blocks.append(block)

    flush_section()
    return chunks


def chunk_markdown(text: str, rules: ChunkRules, source_path: str) -> List[Chunk]:
    normalized = normalize_markdown(text)
    blocks = parse_markdown(normalized)
    return chunk_blocks(blocks, rules, source_path)


def write_chunks(chunks: Sequence[Chunk], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("*.md"):
        path.unlink()
    manifest_path = output_dir / "manifest.jsonl"
    if manifest_path.exists():
        manifest_path.unlink()

    seen_hashes: set[str] = set()
    with manifest_path.open("w", encoding="utf-8") as manifest:
        for chunk in chunks:
            if chunk.chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk.chunk_hash)
            filename = f"{chunk.doc}__{chunk.chunk_hash}.md"
            (output_dir / filename).write_text(chunk.text, encoding="utf-8")
            record = {
                "hash": chunk.chunk_hash,
                "doc": chunk.doc,
                "title_path": chunk.title_path,
                "source_path": chunk.source_path,
                "char_count": chunk.char_count,
            }
            manifest.write(json.dumps(record, ensure_ascii=True) + "\n")
    return manifest_path


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def iter_source_files(config: dict) -> Iterable[Path]:
    chunking = config.get("chunking", {})
    source_globs = chunking.get("source_globs", [])
    exclude_globs = chunking.get("exclude_globs", [])
    for pattern in source_globs:
        for path in Path(".").glob(pattern):
            if path.is_file():
                rel_path = path.relative_to(Path(".")).as_posix()
                if any(fnmatch.fnmatch(rel_path, glob) for glob in exclude_globs):
                    continue
                yield path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=".mini-rag/chunks")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    chunking = config.get("chunking", {})
    rules = ChunkRules(
        chunk_size=int(chunking.get("chunk_size", 800)),
        section_max_chars=int(chunking.get("section_max_chars", 1400)),
        overlap_pct=float(chunking.get("overlap_pct", 0.05)),
    )
    chunks: List[Chunk] = []
    for file_path in iter_source_files(config):
        if file_path.suffix.lower() not in {".md", ".markdown", ".txt", ".yaml", ".yml", ".json"}:
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(chunk_markdown(text, rules, str(file_path)))

    write_chunks(chunks, Path(args.output_dir))


if __name__ == "__main__":
    main()
