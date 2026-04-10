"""Service for Programmatic Context Calling logic (ContextService)."""

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Optional

from src.domain.context_models import ContextChunk, ContextPack, GetResult, SearchHit, SearchResult
from src.domain.result import Err
from src.domain.segment_indexing_policy import SegmentIndexingPolicy
from src.domain.skill_manifest import SkillManifest

SKILL_HUB_PROMOTION_RECEIPT = "skill_hub_promotion_receipt.json"
SKILL_HUB_LAST_VALID_DIR = ".skill_hub_last_valid"


def parse_chunk_id(chunk_id: str) -> tuple[str, str]:
    """
    Parse chunk ID into (kind, rest) with canonical normalization.

    Format: "kind:hash" -> ("kind", "hash") with kind lowercased
    Invalid: "no-colon" -> ("unknown", "no-colon")

    Examples:
        >>> parse_chunk_id("prime:abc123")
        ('prime', 'abc123')
        >>> parse_chunk_id("Prime:abc123")  # Normalized
        ('prime', 'abc123')
        >>> parse_chunk_id("skill:xyz")
        ('skill', 'xyz')
        >>> parse_chunk_id("invalid")
        ('unknown', 'invalid')
    """
    if ":" in chunk_id:
        parts = chunk_id.split(":", 1)
        kind = parts[0].strip().lower()  # Canonical: lowercase
        rest = parts[1]
        return (kind, rest)
    return ("unknown", chunk_id)


class ContextService:
    """Handles ctx.search and ctx.get logic."""

    def __init__(self, target_path: Path):
        self.target_path = target_path
        self.ctx_dir = target_path / "_ctx"
        self.pack_path = self.ctx_dir / "context_pack.json"
        self.policy = SegmentIndexingPolicy.detect(target_path)

    def _load_pack(self) -> ContextPack:
        """Load the context pack from disk."""
        if self.policy == SegmentIndexingPolicy.SKILL_HUB:
            return self._load_skill_hub_promoted_pack()

        if not self.pack_path.exists():
            raise FileNotFoundError(f"Context pack not found at {self.pack_path}")

        with open(self.pack_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ContextPack(**data)

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _load_skill_hub_promoted_pack(self) -> ContextPack:
        errors: list[str] = []

        live_paths = (
            self.ctx_dir / "skills_manifest.json",
            self.ctx_dir / "context_pack.json",
            self.ctx_dir / SKILL_HUB_PROMOTION_RECEIPT,
        )
        promoted_pack = self._validate_and_load_promoted_set(
            *live_paths, source="live", errors=errors
        )
        if promoted_pack is not None:
            return promoted_pack

        backup_dir = self.ctx_dir / SKILL_HUB_LAST_VALID_DIR
        backup_paths = (
            backup_dir / "skills_manifest.json",
            backup_dir / "context_pack.json",
            backup_dir / SKILL_HUB_PROMOTION_RECEIPT,
        )
        promoted_pack = self._validate_and_load_promoted_set(
            *backup_paths, source="last_valid", errors=errors
        )
        if promoted_pack is not None:
            return promoted_pack

        detail = "; ".join(errors) if errors else "runtime artifacts are missing"
        raise RuntimeError(f"No valid promoted set for skill_hub at {self.target_path}. {detail}")

    def _validate_and_load_promoted_set(
        self,
        manifest_path: Path,
        pack_path: Path,
        receipt_path: Path,
        *,
        source: str,
        errors: list[str],
    ) -> ContextPack | None:
        missing_paths = [str(p) for p in (manifest_path, pack_path, receipt_path) if not p.exists()]
        if missing_paths:
            errors.append(f"[{source}] missing artifacts: {', '.join(missing_paths)}")
            return None

        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"[{source}] invalid receipt: {exc}")
            return None

        if not isinstance(receipt, dict):
            errors.append(f"[{source}] invalid receipt shape: expected object")
            return None

        if receipt.get("policy") != SegmentIndexingPolicy.SKILL_HUB.value:
            errors.append(f"[{source}] invalid receipt policy: {receipt.get('policy')!r}")
            return None

        manifest_fingerprint = receipt.get("manifest_fingerprint")
        pack_fingerprint = receipt.get("pack_fingerprint")
        if manifest_fingerprint != self._sha256(manifest_path):
            errors.append(f"[{source}] manifest fingerprint mismatch")
            return None
        if pack_fingerprint != self._sha256(pack_path):
            errors.append(f"[{source}] pack fingerprint mismatch")
            return None

        try:
            raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"[{source}] invalid manifest JSON: {exc}")
            return None
        if not isinstance(raw_manifest, dict) or raw_manifest.get("schema_version") != 2:
            errors.append(f"[{source}] manifest must be canonical schema_version=2")
            return None

        manifest_result = SkillManifest.load(manifest_path, self.target_path)
        if isinstance(manifest_result, Err):
            errors.append(
                f"[{source}] invalid manifest admission: {'; '.join(manifest_result.error)}"
            )
            return None
        manifest = manifest_result.value

        try:
            pack = ContextPack(**json.loads(pack_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"[{source}] invalid context pack JSON: {exc}")
            return None

        pack_admission = SkillManifest.validate_pack_admission(
            manifest,
            declared_policy=SegmentIndexingPolicy.SKILL_HUB.value,
            pack_chunk_ids=[chunk.id for chunk in pack.chunks],
            pack_docs=[chunk.doc for chunk in pack.chunks],
            pack_source_paths=[chunk.source_path for chunk in pack.chunks],
        )
        if isinstance(pack_admission, Err):
            errors.append(f"[{source}] invalid pack admission: {'; '.join(pack_admission.error)}")
            return None

        return pack

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
        max_chunks: Optional[int] = None,
        stop_on_evidence: bool = False,
        query: Optional[str] = None,
    ) -> GetResult:
        """Retrieve chunks by ID with backpressure and progressive disclosure."""
        pack = self._load_pack()
        selected_chunks = []
        total_tokens = 0
        chars_returned_total = 0
        budget = budget_token_est if budget_token_est else 1200

        # Track original request
        chunks_requested = len(ids)

        # Early-stop: max_chunks slicing
        original_ids = ids
        if max_chunks is not None and len(ids) > max_chunks:
            ids = ids[:max_chunks]

        # Create a map for fast lookup
        chunk_map = {c.id: c for c in pack.chunks}

        # Track stop reason and evidence
        stop_reason = "complete"  # Default assumption
        budget_exceeded = False
        evidence_metadata = {"strong_hit": False, "support": False}

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
                    budget_exceeded = True

            token_est = len(text) // 4
            chars_returned_total += len(text)

            # Backpressure: Stop if we are already at budget (or if the first chunk is just too big)
            if total_tokens + token_est > budget and total_tokens > 0:
                stop_reason = "budget"
                break

            new_chunk = chunk.model_copy(update={"text": text, "token_est": token_est})
            selected_chunks.append(new_chunk)
            total_tokens += token_est

            # Evidence-based early-stop
            if stop_on_evidence and query:
                evidence_meta = self._check_evidence(new_chunk, query)
                if evidence_meta["strong_hit"] and evidence_meta["support"]:
                    evidence_metadata = evidence_meta
                    stop_reason = "evidence"
                    break

            if total_tokens >= budget:
                stop_reason = "budget"
                break

        # Determine final stop_reason with explicit precedence:
        # error > evidence > budget > max_chunks > complete
        # Note: "error" is handled by exception catching at higher levels

        # Evidence takes precedence over budget/max_chunks
        if stop_reason == "evidence":
            pass  # Already set, keep it
        # Budget takes precedence over max_chunks
        elif budget_exceeded or stop_reason == "budget":
            stop_reason = "budget"
        # Max_chunks only if budget wasn't exceeded
        elif max_chunks is not None and len(original_ids) > max_chunks:
            stop_reason = "max_chunks"
        # Complete only if all post-sliced IDs were processed successfully
        elif len(selected_chunks) == len(ids):
            stop_reason = "complete"
        # Fallback (should not happen, but defensive)
        else:
            stop_reason = "complete"

        return GetResult(
            chunks=selected_chunks,
            total_tokens=total_tokens,
            stop_reason=stop_reason,
            chunks_requested=chunks_requested,
            chunks_returned=len(selected_chunks),
            chars_returned_total=chars_returned_total,
            evidence_metadata=evidence_metadata,
        )

    def _check_evidence(self, chunk: ContextChunk, query: str) -> dict[str, Any]:
        """
        Check for deterministic evidence signals.

        strong_hit: Query appears in chunk title/id AND chunk ID starts with 'prime:'
        support: Chunk text contains strict patterns 'def <query>(' or 'class <query>:' or 'class <query>('

        Hardened to avoid false positives:
        - Strong hit uses ID prefix pattern (not substring)
        - Support requires exact boundaries (parenthesis or colon)
        - Keyword guard: don't match Python keywords
        """
        # Keyword guard: don't trigger on Python keywords
        python_keywords = {"def", "class", "import", "from", "if", "for", "while", "return"}
        if query.lower() in python_keywords:
            return {"strong_hit": False, "support": False}

        query_lower = query.lower().strip()
        if not query_lower:  # Empty query guard
            return {"strong_hit": False, "support": False}

        chunk_id_lower = chunk.id.lower()
        title_lower = " ".join(chunk.title_path).lower()
        text_lower = chunk.text.lower()

        # Strong hit: query in title/id AND chunk is from prime (typed check)
        kind, _ = parse_chunk_id(chunk_id_lower)
        is_prime = kind == "prime"
        strong_hit = (
            query_lower in chunk_id_lower or query_lower in title_lower
        ) and is_prime  # Support: strict code definition patterns with boundaries
        # Require ( or : after query to avoid "FooBar" matching "Foo"
        support = (
            f"def {query_lower}(" in text_lower
            or f"class {query_lower}(" in text_lower
            or f"class {query_lower}:" in text_lower
        )

        return {"strong_hit": strong_hit, "support": support}

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
