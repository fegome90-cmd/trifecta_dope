#!/usr/bin/env python3
"""
Trifecta Context Pack Builder - Token-Optimized Ingestion

Generates a structured 3-layer Context Pack from markdown files:
- Digest: Summarized content always in prompt (~10-30 lines)
- Index: Chunk references for discovery (ID, title, preview)
- Chunks: Full content delivered on-demand via tools

Usage:
    python ingest_trifecta.py --segment debug_terminal
    python ingest_trifecta.py --segment eval --output custom/pack.json
    python ingest_trifecta.py --segment hemdov --repo-root /path/to/projects
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
SCHEMA_VERSION = 1

# Regex patterns
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")
FENCE_RE = re.compile(r"^(```|~~~)")
YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*$", re.DOTALL)


# =============================================================================
# Normalization Utilities
# =============================================================================

def normalize_markdown(md: str) -> str:
    """Normalize markdown for consistent processing."""
    md = md.replace("\r\n", "\n").strip()
    # Collapse multiple blank lines to double newline
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md + "\n" if md else ""


def normalize_title_path(path: list[str]) -> str:
    """
    Normalize title path for stable ID generation.

    Uses ASCII 0x1F (unit separator) to join titles after:
    - Trimming whitespace
    - Collapsing internal spaces
    - Lowercasing for case-insensitivity
    """
    normalized = []
    for title in path:
        # Trim and collapse whitespace
        title = title.strip().lower()
        title = re.sub(r"\s+", " ", title)
        normalized.append(title)
    return "\x1f".join(normalized)


# =============================================================================
# Hash Utilities
# =============================================================================

def sha256_text(s: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def generate_chunk_id(doc: str, title_path: list[str], text: str) -> str:
    """
    Generate stable chunk ID from normalized components.

    The ID is deterministic and stable across runs:
    - Same doc + title_path + text_hash → same ID
    - Changes in doc A don't affect IDs in doc B
    - Whitespace changes in headings don't change IDs (due to normalization)

    Format: "{doc}:{10-char-hash}"
    """
    text_hash = sha256_text(text)
    seed = f"{doc}\n{normalize_title_path(title_path)}\n{text_hash}"
    chunk_hash = hashlib.sha1(seed.encode()).hexdigest()[:10]
    return f"{doc}:{chunk_hash}"


# =============================================================================
# Preview & Token Estimation
# =============================================================================

def preview(text: str, max_chars: int = 180) -> str:
    """Generate one-line preview of chunk content."""
    # Collapse all whitespace to single space
    one_liner = re.sub(r"\s+", " ", text.strip())
    return one_liner[:max_chars] + ("…" if len(one_liner) > max_chars else "")


def estimate_tokens(text: str) -> int:
    """Rough token estimation: 1 token ≈ 4 characters."""
    return len(text) // 4


# =============================================================================
# Chunk Scoring for Digest
# =============================================================================

def score_chunk(title: str, level: int, text: str) -> int:
    """
    Score a chunk for digest inclusion.

    Higher scores = more relevant for digest.
    Returns integer score (can be negative).
    """
    score = 0
    title_lower = title.lower()

    # Keywords that indicate relevance
    relevant_keywords = [
        "core", "rules", "workflow", "commands",
        "usage", "setup", "api", "architecture",
        "critical", "mandatory", "protocol"
    ]
    if any(kw in title_lower for kw in relevant_keywords):
        score += 3

    # Higher headings (level 1-2) are more important
    if level <= 2:
        score += 2

    # Penalize empty/fluff sections
    fluff_keywords = ["overview", "intro", "introduction"]
    if any(kw in title_lower for kw in fluff_keywords) and len(text) < 300:
        score -= 2

    return score


# =============================================================================
# Fence-Aware Chunking
# =============================================================================

def chunk_by_headings_fence_aware(
    doc_id: str,
    md: str,
    max_chars: int = 6000
) -> list[dict]:
    """
    Split markdown into chunks using headings, respecting code fences.

    State machine tracks `in_fence` to avoid splitting inside code blocks.
    Oversized sections are split by paragraphs as fallback.

    Args:
        doc_id: Document identifier (e.g., "skill")
        md: Normalized markdown content
        max_chars: Maximum characters per chunk before paragraph fallback

    Returns:
        List of chunk dictionaries with metadata
    """
    lines = md.splitlines()
    chunks = []

    # Current chunk state
    title = "INTRO"
    title_path: list[str] = []
    level = 0
    start_line = 0
    buf: list[str] = []
    in_fence = False

    def flush(end_line: int) -> None:
        nonlocal title, level, start_line, buf
        if buf:
            text = "\n".join(buf).strip()
            if text:
                chunks.append({
                    "title": title,
                    "title_path": title_path.copy(),
                    "heading_level": level,  # FIX: use heading_level consistently
                    "text": text,
                    "start_line": start_line + 1,  # 1-indexed
                    "end_line": end_line,
                })
            buf = []
            start_line = end_line + 1

    for i, line in enumerate(lines):
        # Check for code fence
        fence_match = FENCE_RE.match(line)
        if fence_match:
            in_fence = not in_fence
            buf.append(line)
            continue

        # Check for heading (only outside fences)
        heading_match = HEADING_RE.match(line)
        if heading_match and not in_fence:
            # Flush previous chunk
            flush(i)

            # Start new chunk
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            title_path = title_path[:level - 1] + [title]  # Maintain hierarchy
            start_line = i
            buf = [line]
        else:
            buf.append(line)

    # Flush final chunk
    flush(len(lines))

    # Split oversized chunks by paragraphs
    final_chunks = []
    for chunk in chunks:
        text = chunk["text"]
        if len(text) <= max_chars:
            final_chunks.append(chunk)
            continue

        # Split by paragraphs (fence-aware)
        # FIX: Don't split inside code fences
        lines = text.splitlines()
        paragraphs = []
        current_para = []
        in_fence_para = False

        for line in lines:
            if FENCE_RE.match(line):
                in_fence_para = not in_fence_para
                current_para.append(line)
            elif not line.strip() and not in_fence_para:
                # Empty line outside fence = paragraph break
                if current_para:
                    paragraphs.append("\n".join(current_para))
                    current_para = []
            else:
                current_para.append(line)

        if current_para:
            paragraphs.append("\n".join(current_para))

        # Now split oversized chunk by paragraphs
        acc: list[str] = []
        acc_len = 0
        part_num = 1

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if acc and acc_len + len(para) + 2 > max_chars:
                # Flush accumulated paragraphs
                final_chunks.append({
                    **chunk,
                    "title": f"{chunk['title']} (part {part_num})",
                    "text": "\n\n".join(acc),
                })
                acc = []
                acc_len = 0
                part_num += 1

            acc.append(para)
            acc_len += len(para) + 2  # +2 for "\n\n"

        # Flush remaining
        if acc:
            final_chunks.append({
                **chunk,
                "title": f"{chunk['title']} (part {part_num})",
                "text": "\n\n".join(acc),
            })

    return final_chunks


# =============================================================================
# Context Pack Builder
# =============================================================================

class ContextPackBuilder:
    """Builds token-optimized Context Pack from markdown files."""

    def __init__(self, segment: str, repo_root: Path):
        self.segment = segment
        self.repo_root = repo_root
        self.segment_path = repo_root / segment

    def find_markdown_files(self) -> list[Path]:
        """Find all markdown files in the segment."""
        files = []
        for pattern in ["*.md", "_ctx/*.md"]:
            files.extend(self.segment_path.glob(pattern))
        return sorted(f for f in files if f.is_file())

    def load_document(self, path: Path) -> tuple[str, str]:
        """
        Load and parse markdown document.

        Returns:
            (doc_id, normalized_content)
        """
        doc_id = path.stem
        # Handle _ctx/ prefix
        if "_ctx/" in str(path):
            doc_id = path.stem  # prime_debug-terminal, session_debug-terminal, agent

        raw = path.read_text(encoding="utf-8")

        # Remove YAML frontmatter
        match = YAML_FRONTMATTER_RE.match(raw)
        if match:
            raw = raw[match.end():]

        return doc_id, normalize_markdown(raw)

    def build_chunks(self, doc_id: str, content: str, source_path: Path) -> list[dict]:
        """Build chunks with stable IDs and metadata."""
        raw_chunks = chunk_by_headings_fence_aware(doc_id, content)

        chunks = []
        for chunk in raw_chunks:
            chunk_id = generate_chunk_id(doc_id, chunk["title_path"], chunk["text"])
            chunks.append({
                "id": chunk_id,
                "doc": doc_id,
                "title_path": chunk["title_path"],
                "text": chunk["text"],
                "source_path": str(source_path.relative_to(self.repo_root)),
                "heading_level": chunk["heading_level"],
                "char_count": len(chunk["text"]),
                "line_count": chunk["text"].count("\n") + 1,
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            })

        return chunks

    def build_digest(self, doc_id: str, chunks: list[dict]) -> dict:
        """
        Build deterministic digest entry.

        Selects top-2 most relevant chunks per doc (max 1200 chars total).
        Extracts first N lines from selected chunks as actual digest text.
        """
        # Score all chunks
        scored = []
        for chunk in chunks:
            title = chunk["title_path"][-1] if chunk["title_path"] else "Introduction"
            score = score_chunk(
                title,
                chunk["heading_level"],
                chunk["text"]
            )
            scored.append((score, chunk))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Select top chunks within budget (iterate ALL, not just [:2])
        selected_chunks = []
        total_chars = 0
        for score, chunk in scored:  # FIX: iterate all, not [:2]
            if total_chars + chunk["char_count"] > 1200:
                continue  # FIX: continue, not break
            selected_chunks.append(chunk)
            total_chars += chunk["char_count"]
            if len(selected_chunks) >= 2:  # Stop after 2 chunks
                break

        # Build digest text (extract first N lines, not just titles)
        digest_lines = []
        for c in selected_chunks:
            # Extract first 10 non-empty lines from chunk
            lines = [line.strip() for line in c["text"].split("\n") if line.strip()]
            digest_lines.extend(lines[:10])

        digest_text = "\n".join(digest_lines[:30])  # Max 30 lines total

        return {
            "doc": doc_id,
            "summary": digest_text,  # FIX: actual text, not TOC
            "source_chunk_ids": [c["id"] for c in selected_chunks],
        }

    def build(self, output_path: Path | None = None) -> dict:
        """
        Build complete Context Pack.

        Args:
            output_path: Optional custom output path

        Returns:
            Complete context pack dictionary
        """
        md_files = self.find_markdown_files()

        if not md_files:
            raise ValueError(f"No markdown files found in {self.segment_path}")

        # Load all documents
        docs = []
        all_chunks = []

        for path in md_files:
            doc_id, content = self.load_document(path)
            chunks = self.build_chunks(doc_id, content, path)

            docs.append({
                "doc": doc_id,
                "file": path.name,
                "sha256": sha256_text(content),
                "chunk_count": len(chunks),
                "total_chars": len(content),
            })
            all_chunks.extend(chunks)

        # Build index (digest is separate)
        index = []
        for chunk in all_chunks:
            index.append({
                "id": chunk["id"],
                "doc": chunk["doc"],
                "title_path": chunk["title_path"],
                "preview": preview(chunk["text"]),
                "token_est": estimate_tokens(chunk["text"]),
                "source_path": chunk["source_path"],
                "heading_level": chunk["heading_level"],
                "char_count": chunk["char_count"],
                "line_count": chunk["line_count"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            })

        # Build digest (top chunks per doc)
        digest = []
        for doc in docs:
            doc_chunks = [c for c in all_chunks if c["doc"] == doc["doc"]]
            if doc_chunks:
                digest.append(self.build_digest(doc["doc"], doc_chunks))

        # Assemble pack
        pack = {
            "schema_version": SCHEMA_VERSION,
            "segment": self.segment,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": VERSION,
            "source_files": [
                {
                    "path": str(f.relative_to(self.repo_root)),
                    "sha256": sha256_text(f.read_text(encoding="utf-8")),
                    "mtime": int(f.stat().st_mtime),
                    "chars": len(f.read_text(encoding="utf-8")),
                    "size": f.stat().st_size,
                }
                for f in md_files
            ],
            "chunking": {
                "method": "headings+paragraph_fallback+fence_aware",
                "max_chars": 6000,
            },
            "docs": docs,
            "digest": digest,
            "index": index,
            "chunks": all_chunks,
        }

        # Write to disk
        if output_path is None:
            output_path = self.segment_path / "_ctx" / "context_pack.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(pack, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return pack


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate token-optimized Context Pack from Trifecta documentation",
        epilog="""Examples:
  python ingest_trifecta.py --segment debug_terminal
  python ingest_trifecta.py --segment hemdov --repo-root /path/to/projects
  python ingest_trifecta.py --segment eval --output custom/pack.json --dry-run""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--segment",
        "-s",
        required=True,
        help="Segment name (e.g., debug_terminal, eval, hemdov)",
    )
    parser.add_argument(
        "--repo-root",
        "-r",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: cwd)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Custom output path (default: {segment}/_ctx/context_pack.json)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview without writing output file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed processing information",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force regeneration even if output exists and is up-to-date",
    )

    args = parser.parse_args()

    try:
        # FIX #5: Validate segment name (prevent path traversal)
        if not re.match(r'^[a-zA-Z0-9_-]+$', args.segment):
            raise ValueError(
                f"Invalid segment name: '{args.segment}'\n"
                f"Segment must contain only alphanumeric characters, underscores, and hyphens."
            )

        builder = ContextPackBuilder(args.segment, args.repo_root)

        # Validate segment exists
        if not builder.segment_path.exists():
            raise ValueError(f"Segment path does not exist: {builder.segment_path}")

        # Validate segment path is within repo_root (prevent traversal)
        try:
            builder.segment_path.resolve().relative_to(args.repo_root.resolve())
        except ValueError:
            raise ValueError(
                f"Segment path is outside repository root:\n"
                f"  Segment: {builder.segment_path}\n"
                f"  Repo root: {args.repo_root}"
            )

        if args.verbose:
            print(f"[verbose] Segment: {args.segment}", file=sys.stderr)
            print(f"[verbose] Repo root: {args.repo_root}", file=sys.stderr)
            print(f"[verbose] Segment path: {builder.segment_path}", file=sys.stderr)

        # Build pack
        pack = builder.build(args.output if not args.dry_run else None)

        chunk_count = len(pack["chunks"])
        output_path = args.output or (args.repo_root / args.segment / "_ctx" / "context_pack.json")

        if args.dry_run:
            print(
                f"[dry-run] Would generate Context Pack:\n"
                f"    • {chunk_count} chunks\n"
                f"    • {len(pack['digest'])} digest entries\n"
                f"    • {len(pack['index'])} index entries\n"
                f"    → {output_path} (not written)",
                file=sys.stderr
            )
        else:
            print(
                f"[ok] Context Pack generated:\n"
                f"    • {chunk_count} chunks\n"
                f"    • {len(pack['digest'])} digest entries\n"
                f"    • {len(pack['index'])} index entries\n"
                f"    → {output_path}",
                file=sys.stderr
            )

        if args.verbose:
            # Show digest entries
            print("\n[verbose] Digest entries:", file=sys.stderr)
            for d in pack["digest"]:
                print(f"  - {d['doc']}: {d['summary']}", file=sys.stderr)

            # Show sample chunk IDs
            print("\n[verbose] Sample chunk IDs:", file=sys.stderr)
            for c in pack["chunks"][:3]:
                title = " → ".join(c["title_path"]) if c["title_path"] else "INTRO"
                print(f"  - {c['id']}: {title} ({c['char_count']} chars)", file=sys.stderr)

    except ValueError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[interrupted] Operation cancelled", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[error] Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
