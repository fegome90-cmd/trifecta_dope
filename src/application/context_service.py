"""Service for Programmatic Context Calling logic."""

import json
from pathlib import Path
from typing import Literal, Optional

from src.domain.context_models import ContextPack, GetResult, SearchHit, SearchResult


class ContextService:
    """Handles ctx.search and ctx.get logic."""

    def __init__(self, target_path: Path):
        self.target_path = target_path
        self.ctx_dir = target_path / "_ctx"
        self.pack_path = self.ctx_dir / "context_pack.json"

    def _load_pack(self) -> ContextPack:
        """Load the context pack from disk."""
        if not self.pack_path.exists():
            raise FileNotFoundError(f"Context pack not found at {self.pack_path}")

        with open(self.pack_path, "r") as f:
            data = json.load(f)
            return ContextPack(**data)

    def search(self, query: str, k: int = 5, doc_filter: Optional[str] = None) -> SearchResult:
        """
        Simple heuristic search for chunks.
        MVP: Keyword matching in previews/titles.
        """
        pack = self._load_pack()
        hits = []
        query_words = [w.lower() for w in query.split() if len(w) > 2]  # Skip short words

        if not query_words:
            query_words = [query.lower()]

        for entry in pack.index:
            # Apply doc filter if provided
            if doc_filter and doc_filter not in entry.id:
                continue

            score = 0.0
            title_lower = entry.title_path_norm.lower()
            preview_lower = entry.preview.lower()

            # 1. Direct word matches
            for word in query_words:
                if word in title_lower:
                    score += 1.0
                if word in preview_lower:
                    score += 0.5

            # 2. Heuristic boosts (Even if title/preview match failed)
            if "skill" in entry.id and any(
                kw in query_words for kw in ["regla", "comando", "cómo", "rule", "protocol"]
            ):
                score += 0.5
            if "agent" in entry.id and any(
                kw in query_words for kw in ["stack", "código", "tech", "implement", "debug", "fix"]
            ):
                score += 1.0
            if "session" in entry.id and any(
                kw in query_words
                for kw in ["pasos", "checklist", "runbook", "handoff", "history", "log"]
            ):
                score += 0.8

            if score > 0:
                hits.append(
                    SearchHit(
                        id=entry.id,
                        title_path=[entry.title_path_norm],
                        preview=entry.preview,
                        token_est=entry.token_est,
                        source_path=entry.title_path_norm,
                        score=score,
                    )
                )

        # Sort by score and take top k
        hits = sorted(hits, key=lambda x: x.score, reverse=True)[:k]
        return SearchResult(hits=hits)

    def get(
        self,
        ids: list[str],
        mode: Literal["raw", "excerpt", "skeleton"] = "raw",
        budget_token_est: Optional[int] = None,
    ) -> GetResult:
        """Retrieve chunks by ID with backpressure and progressive disclosure."""
        pack = self._load_pack()
        selected_chunks = []
        total_tokens = 0
        budget = budget_token_est if budget_token_est else 1200

        # Create a map for fast lookup
        chunk_map = {c.id: c for c in pack.chunks}

        for chunk_id in ids:
            chunk = chunk_map.get(chunk_id)
            if not chunk:
                continue

            # Progressive Disclosure logic
            text = chunk.text
            if mode == "excerpt":
                # T4: headings + trimming + first 25 lines
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                excerpt_lines = lines[:25]
                text = "\n".join(excerpt_lines)
                if len(lines) > 25:
                    text += "\n\n... [Contenido truncado, usa mode='raw' para ver todo]"
            elif mode == "skeleton":
                text = self._skeletonize(text)
            elif mode == "raw":
                # T4: check if it fits in budget
                token_est = len(text) // 4
                if total_tokens + token_est > budget:
                    # Fallback to excerpt with note
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    text = (
                        "\n".join(lines[:20])
                        + "\n\n> [!NOTE]\n> Chunk truncado por presupuesto de tokens. Usa mode='raw' con mayor budget si es crítico."
                    )

            token_est = len(text) // 4

            # Backpressure: Stop if we are already at budget (or if the first chunk is just too big)
            if total_tokens + token_est > budget and total_tokens > 0:
                break

            new_chunk = chunk.model_copy(update={"text": text, "token_est": token_est})
            selected_chunks.append(new_chunk)
            total_tokens += token_est

            if total_tokens >= budget:
                break

        return GetResult(chunks=selected_chunks, total_tokens=total_tokens)

    def _skeletonize(self, text: str) -> str:
        """
        Extract headings and code block markers to create a structure view.
        """
        skeleton_lines = []
        in_code_block = False

        for line in text.splitlines():
            line_strip = line.strip()

            # Keep headings
            if line_strip.startswith("#"):
                skeleton_lines.append(line)
                continue

            # Keep code block markers
            if line_strip.startswith("```"):
                skeleton_lines.append(line)
                in_code_block = not in_code_block
                continue

            # If inside code block, keep first line (signature)
            if (
                in_code_block
                and len(skeleton_lines) > 0
                and skeleton_lines[-1].strip().startswith("```")
            ):
                if any(
                    kw in line
                    for kw in ["def ", "class ", "interface ", "function ", "const ", "var "]
                ):
                    skeleton_lines.append(f"  {line_strip}")

        if not skeleton_lines:
            return text[:200] + "..."  # Fallback

        return "\n".join(skeleton_lines)
