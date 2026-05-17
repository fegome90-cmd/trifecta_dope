from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from scripts.skill_hub_runtime_ux import RuntimeSkillCard

try:
    from src.application.skill_card_view_model import SkillCardViewModel  # noqa: F401 — re-export for consumers
except ImportError:
    pass

try:
    from scripts.skill_hub_runtime_ux import RuntimeSkillCard as _RuntimeSkillCard
except ImportError:
    from skill_hub_runtime_ux import RuntimeSkillCard as _RuntimeSkillCard  # type: ignore[no-redef]

TRIFECTA_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEGMENT_PATH = Path.home() / ".trifecta" / "segments" / "skills-hub"

EXIT_RENDERABLE = 0
EXIT_ERROR = 1
EXIT_NON_RENDERABLE = 3
EXIT_EMPTY = 4

_METADATA_RAW_TYPES = {"session", "agent", "prime"}
_RENDERABLE_RAW_TYPES = {"repo", "skill"}
_DESCRIPTION_PATTERNS = (
    r"^(Use when.+)$",
    r"^(Use for.+)$",
    r"^(Trigger when.+)$",
    r"^\*\*description\*\*:\s*(.+)$",
    r"^description:\s*(.+)$",
)
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


class OutcomeKind(StrEnum):
    RENDERABLE_SKILL = "renderable_skill"
    METADATA_ONLY = "metadata_only"
    UNSUPPORTED = "unsupported"
    EMPTY = "empty"


@dataclass(frozen=True)
class RawSearchHit:
    ref: str
    raw_type: str
    title: str
    score: float


@dataclass(frozen=True)
class NormalizedResult:
    ref: str
    raw_type: str
    raw_title: str
    score: float
    stable_id: str | None
    visible_title: str | None
    path: str | None
    source: str | None
    description: str | None
    metadata_message: str | None
    metadata_reason: str | None


@dataclass(frozen=True)
class ClassifiedResult:
    kind: OutcomeKind
    normalized: NormalizedResult
    reason: str
    authority_state: str = "healthy"


def SkillCard(*, id: str, title: str, path: str, source: str, description: str, score: float) -> _RuntimeSkillCard:
    """Backward-compatible factory function mapping title→name, score→relevance."""
    return _RuntimeSkillCard(
        id=id,
        name=title,
        path=path,
        source=source,
        description=description,
        relevance=score,
    )


@dataclass(frozen=True)
class RenderPlan:
    outcome_kind: OutcomeKind
    exit_code: int
    cards: list[_RuntimeSkillCard]
    message: str
    classified_results: list[ClassifiedResult]


class SearchRuntimeError(RuntimeError):
    def __init__(self, message: str, elapsed_seconds: float = 0.0, partial_results: str | None = None) -> None:
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds
        self.partial_results = partial_results


class GetRuntimeError(RuntimeError):
    def __init__(self, message: str, elapsed_seconds: float = 0.0, partial_results: str | None = None) -> None:
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds
        self.partial_results = partial_results


class SearchParseError(RuntimeError):
    pass


# Bidi control characters to strip from queries
_BIDI_CHARS = frozenset(
    "\u202e\u200f\u202a\u202b\u202c\u202d\u2066\u2067\u2068\u2069"
)


def sanitize_query(query: str, *, max_length: int = 500) -> str:
    """Strip dangerous characters and enforce length limits on search queries.

    Removes null bytes, BOM, and bidirectional control characters.
    Truncates queries exceeding *max_length*, appending ``"..."``.
    Raises :class:`ValueError` on empty or whitespace-only input.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty or whitespace-only")
    # Strip null bytes
    cleaned = query.replace("\x00", "")
    # Strip BOM
    cleaned = cleaned.replace("\ufeff", "")
    # Strip bidi control chars
    cleaned = "".join(ch for ch in cleaned if ch not in _BIDI_CHARS)
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    if not cleaned:
        raise ValueError("Query cannot be empty or whitespace-only")
    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    return cleaned


# --- Adapter: ClassifiedResult → RuntimeSkillCard ---

_TRUSTED_FIELDS = ("stable_id", "visible_title", "path", "source", "description")


def build_view_model(result: ClassifiedResult):
    """Bridge classified result to the render model.

    Returns None when kind != RENDERABLE_SKILL.
    authority_state comes from ClassifiedResult.
    fidelity_level derived from field completeness.
    """
    if result.kind != OutcomeKind.RENDERABLE_SKILL:
        return None

    normalized = result.normalized
    present_count = sum(1 for f in _TRUSTED_FIELDS if getattr(normalized, f, None) is not None)

    if present_count >= 5:
        fidelity_level = "full"
    elif present_count >= 3:
        fidelity_level = "partial"
    else:
        fidelity_level = "minimal"

    return _RuntimeSkillCard(
        id=normalized.stable_id or "",
        name=normalized.visible_title or normalized.stable_id or "",
        path=normalized.path or "",
        source=normalized.source or "",
        description=normalized.description or "",
        authority_state=result.authority_state,
        fidelity_level=fidelity_level,
        compact_flag=fidelity_level != "full",
        relevance=normalized.score,
        synthetic=(normalized.path is None and normalized.source is None and normalized.description is None),
    )


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"\.md$", "", lowered)
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-")


def parse_search_output(raw_output: str, *, strict_json: bool = False) -> list[RawSearchHit]:
    text = raw_output.strip()
    if not text:
        return []

    looks_like_json = _looks_like_json_payload(text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        if strict_json or looks_like_json:
            raise SearchParseError("parse error: invalid JSON search payload") from exc
        return _parse_plain_search_output(text)

    if not isinstance(payload, dict):
        if strict_json or looks_like_json:
            raise SearchParseError("parse error: search payload must be a JSON object")
        return _parse_plain_search_output(text)

    hits = payload.get("hits", [])
    if not isinstance(hits, list):
        raise SearchParseError("invalid hits list in search JSON payload")

    parsed: list[RawSearchHit] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        ref = str(hit.get("ref", "")).strip()
        if not ref:
            continue
        raw_type = ref.split(":", 1)[0]
        try:
            score = float(hit.get("score", 0.0) or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        parsed.append(
            RawSearchHit(
                ref=ref,
                raw_type=raw_type,
                title=_title_from_ref(ref),
                score=score,
            )
        )
    return parsed


def _parse_plain_search_output(text: str) -> list[RawSearchHit]:
    results: list[RawSearchHit] = []
    matches = list(re.finditer(r"^\d+\.\s+\[([^\]]+)\]\s+(.+)$", text, re.MULTILINE))
    for index, match in enumerate(matches):
        ref = match.group(1).strip()
        title = match.group(2).strip()
        raw_type = ref.split(":", 1)[0] if ":" in ref else "unsupported"
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        score_match = re.search(r"Score:\s*([\d.]+)", block)
        try:
            score = float(score_match.group(1)) if score_match else 0.0
        except ValueError:
            score = 0.0
        results.append(RawSearchHit(ref=ref, raw_type=raw_type, title=title, score=score))
    return results


def normalize_result(hit: RawSearchHit, chunk_text: str) -> NormalizedResult:
    clean_chunk = chunk_text.strip()
    if hit.raw_type in _METADATA_RAW_TYPES or _looks_like_metadata(clean_chunk):
        return NormalizedResult(
            ref=hit.ref,
            raw_type=hit.raw_type,
            raw_title=hit.title,
            score=hit.score,
            stable_id=None,
            visible_title=_extract_heading(clean_chunk) or hit.title,
            path=None,
            source=None,
            description=None,
            metadata_message=_metadata_message(clean_chunk, hit.raw_type),
            metadata_reason="administrative metadata is not an executable skill",
        )

    path = _extract_path(clean_chunk)
    explicit_title = _extract_skill_title(clean_chunk)
    preferred_title = explicit_title or _title_from_ref(hit.ref) or _title_from_path(path) or hit.title
    visible_title = preferred_title
    stable_id = slugify(preferred_title)
    source = _extract_source(clean_chunk) or _infer_source_from_path(path)
    description = _extract_useful_description(clean_chunk)

    return NormalizedResult(
        ref=hit.ref,
        raw_type=hit.raw_type,
        raw_title=hit.title,
        score=hit.score,
        stable_id=stable_id or None,
        visible_title=visible_title or None,
        path=path,
        source=source,
        description=description,
        metadata_message=None,
        metadata_reason=None,
    )


def classify_result(normalized: NormalizedResult) -> ClassifiedResult:
    if normalized.raw_type in _METADATA_RAW_TYPES or normalized.metadata_message:
        return ClassifiedResult(
            kind=OutcomeKind.METADATA_ONLY,
            normalized=normalized,
            reason=normalized.metadata_reason
            or "administrative metadata is not renderable as a skill card",
        )

    if normalized.raw_type not in _RENDERABLE_RAW_TYPES:
        return ClassifiedResult(
            kind=OutcomeKind.UNSUPPORTED,
            normalized=normalized,
            reason=f"raw type '{normalized.raw_type}' is not supported for skill card rendering",
        )

    has_confident_repo_promotion = all(
        [
            normalized.stable_id,
            normalized.visible_title,
            normalized.path,
            normalized.source,
            normalized.description,
        ]
    )
    if has_confident_repo_promotion:
        return ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=normalized,
            reason="sufficient trusted fields available for skill card rendering",
            authority_state="healthy",
        )

    # Partial fields: still renderable but degraded (needs at minimum stable_id)
    if normalized.stable_id:
        return ClassifiedResult(
            kind=OutcomeKind.RENDERABLE_SKILL,
            normalized=normalized,
            reason="partial trusted fields — degraded skill card",
            authority_state="degraded",
        )

    return ClassifiedResult(
        kind=OutcomeKind.UNSUPPORTED,
        normalized=normalized,
        reason="result could not be promoted safely to a skill card",
    )


def build_render_plan(
    raw_search_output: str,
    chunk_texts: dict[str, str],
    limit: int = 5,
    *,
    strict_json: bool = False,
) -> RenderPlan:
    validated_limit = _validate_positive_limit(limit)
    hits = parse_search_output(raw_search_output, strict_json=strict_json)
    if not hits:
        return RenderPlan(
            outcome_kind=OutcomeKind.EMPTY,
            exit_code=EXIT_EMPTY,
            cards=[],
            message="No search hits found.",
            classified_results=[],
        )

    classified_results = [
        classify_result(normalize_result(hit, chunk_texts.get(hit.ref, "")))
        for hit in hits[:validated_limit]
    ]
    cards: list[_RuntimeSkillCard] = [
        vm
        for result in classified_results
        if result.kind == OutcomeKind.RENDERABLE_SKILL
        if (vm := build_view_model(result)) is not None
    ]

    if cards:
        exit_code = EXIT_EMPTY if all(card.synthetic for card in cards) else EXIT_RENDERABLE
        return RenderPlan(
            outcome_kind=OutcomeKind.RENDERABLE_SKILL,
            exit_code=exit_code,
            cards=cards,
            message="",
            classified_results=classified_results,
        )

    if classified_results and all(result.kind == OutcomeKind.METADATA_ONLY for result in classified_results):
        return RenderPlan(
            outcome_kind=OutcomeKind.METADATA_ONLY,
            exit_code=EXIT_NON_RENDERABLE,
            cards=[],
            message="Administrative metadata found, but it is not renderable as a skill card.",
            classified_results=classified_results,
        )

    return RenderPlan(
        outcome_kind=OutcomeKind.UNSUPPORTED,
        exit_code=EXIT_NON_RENDERABLE,
        cards=[],
        message="Search returned hits, but they could not be promoted safely to a skill card.",
        classified_results=classified_results,
    )


def run_search(query: str, limit: int, *, segment_path: Path | None = None, timeout: int | None = 30) -> str:
    resolved = segment_path or DEFAULT_SEGMENT_PATH
    env = os.environ.copy()
    env.update({"TRIFECTA_LINT": "1", "TRIFECTA_NO_TELEMETRY": "1"})
    start = time.monotonic()
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "trifecta",
                "ctx",
                "search",
                "--segment",
                str(resolved),
                "--query",
                query,
                "--limit",
                str(limit),
                "--explain",
                "--explain-format",
                "json",
            ],
            cwd=str(TRIFECTA_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        elapsed_seconds = time.monotonic() - start
        partial = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode() if e.stdout else None)
        raise SearchRuntimeError(
            f"Search timed out after {elapsed_seconds:.1f}s (limit: {timeout}s)",
            elapsed_seconds=elapsed_seconds,
            partial_results=partial,
        ) from e
    if result.returncode != 0:
        raise SearchRuntimeError(
            result.stderr.strip() or result.stdout.strip() or "unknown search error"
        )
    return result.stdout


def run_get(chunk_ids: Iterable[str], *, segment_path: Path | None = None, timeout: int | None = 30) -> dict[str, str]:
    resolved = segment_path or DEFAULT_SEGMENT_PATH
    refs = [chunk_id for chunk_id in chunk_ids if chunk_id]
    if not refs:
        return {}

    env = os.environ.copy()
    env.update({"TRIFECTA_LINT": "1", "TRIFECTA_NO_TELEMETRY": "1"})
    start = time.monotonic()
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "trifecta",
                "ctx",
                "get",
                "--segment",
                str(resolved),
                "--ids",
                ",".join(refs),
                "--mode",
                "excerpt",
            ],
            cwd=str(TRIFECTA_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        elapsed_seconds = time.monotonic() - start
        partial = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode() if e.stdout else None)
        raise GetRuntimeError(
            f"Get timed out after {elapsed_seconds:.1f}s (limit: {timeout}s)",
            elapsed_seconds=elapsed_seconds,
            partial_results=partial,
        ) from e
    if result.returncode != 0:
        raise GetRuntimeError(result.stderr.strip() or result.stdout.strip() or "unknown get error")
    return _parse_get_output(result.stdout)


_PUBLIC_CARD_FIELDS = ("id", "name", "path", "source", "description", "authority_state", "relevance", "synthetic")


def output_json(plan: RenderPlan) -> str:
    payload = {
        "outcome_kind": plan.outcome_kind.value,
        "exit_code": plan.exit_code,
        "message": plan.message,
        "cards": [{f: getattr(card, f) for f in _PUBLIC_CARD_FIELDS} for card in plan.cards],
        "classified_results": [
            {
                "kind": item.kind.value,
                "ref": item.normalized.ref,
                "raw_type": item.normalized.raw_type,
                "reason": item.reason,
            }
            for item in plan.classified_results
        ],
    }
    return json.dumps(payload, indent=2)


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Governed skill card renderer.")
    parser.add_argument("query", nargs="?", help="Search query for governed card rendering")
    parser.add_argument(
        "--limit", "-l", type=_positive_int, default=5, help="Max cards / hits to evaluate (default: 5)"
    )
    parser.add_argument(
        "--segment",
        type=Path,
        default=None,
        help="Path to skills-hub segment (default: ~/.trifecta/segments/skills-hub)",
    )
    parser.add_argument(
        "--style", choices=["plain", "rich"], default="plain", help="Output style (default: plain)"
    )
    parser.add_argument(
        "--json", "-j", action="store_true", help="Emit structured JSON instead of rendered output"
    )
    parser.add_argument(
        "--stdin-search-output",
        action="store_true",
        help="Read legacy search output from stdin instead of executing governed search",
    )
    args = parser.parse_args(argv)
    # Sanitize query before any processing (skip for stdin mode — no query to sanitize)
    if not args.stdin_search_output:
        if args.query is None or not args.query.strip():
            print("❌ Query rejected: Query cannot be empty or whitespace-only", file=sys.stderr)
            return EXIT_EMPTY
        try:
            args.query = sanitize_query(args.query)
        except ValueError:
            print("❌ Query rejected: Query cannot be empty or whitespace-only", file=sys.stderr)
            return EXIT_EMPTY

    segment_path = args.segment
    try:
        validated_limit = _validate_positive_limit(args.limit)
    except ValueError as exc:
        print(f"skill-hub-cards: {exc}", file=sys.stderr)
        return EXIT_ERROR

    try:
        raw_search_output = _load_search_payload(args, segment_path=segment_path)
        strict_json = args.stdin_search_output and _looks_like_json_payload(raw_search_output)
        hits = parse_search_output(raw_search_output, strict_json=strict_json)
        chunk_texts = run_get((hit.ref for hit in hits[:validated_limit]), segment_path=segment_path)
        plan = build_render_plan(
            raw_search_output, chunk_texts, limit=validated_limit, strict_json=strict_json
        )
    except (SearchRuntimeError, GetRuntimeError, SearchParseError) as exc:
        print(f"skill-hub-cards: {exc}", file=sys.stderr)
        return EXIT_ERROR

    is_tty = sys.stdout.isatty()
    rendered = _select_renderer(plan, use_json=args.json, style=args.style, is_tty=is_tty)
    stream = sys.stdout if plan.outcome_kind == OutcomeKind.RENDERABLE_SKILL else sys.stderr
    if rendered:
        if not args.json and plan.outcome_kind == OutcomeKind.RENDERABLE_SKILL:
            runtime_ux = _import_runtime_ux("skill_hub_runtime_ux")
            print(
                runtime_ux.render_intro(query_hint=args.query, rich=is_tty and args.style == "rich"),
                file=stream,
            )
        print(rendered, file=stream)
    return plan.exit_code


def _import_runtime_ux(module: str):
    try:
        return __import__(f"scripts.{module}", fromlist=[module])
    except ImportError:
        return __import__(module)


def _select_renderer(plan: RenderPlan, *, use_json: bool, style: str, is_tty: bool = True) -> str:
    if use_json:
        return output_json(plan)
    mod = _import_runtime_ux("skill_hub_runtime_ux")
    use_rich = style == "rich" or (style != "plain" and is_tty)
    if plan.cards and use_rich:
        return mod.render_cards_rich(plan.cards)
    if plan.cards:
        return mod.render_cards_plain(plan.cards)
    return mod.render_non_renderable_message(
        outcome_kind=plan.outcome_kind.value, message=plan.message
    )


def _load_search_payload(args: argparse.Namespace, *, segment_path: Path | None = None) -> str:
    if args.stdin_search_output or (not args.query and not sys.stdin.isatty()):
        return sys.stdin.read()
    if not args.query:
        raise SearchRuntimeError("query required unless --stdin-search-output is provided")
    return run_search(args.query, args.limit, segment_path=segment_path)


def _parse_get_output(output: str) -> dict[str, str]:
    chunks: dict[str, str] = {}
    current_ref: str | None = None
    current_lines: list[str] = []

    for line in output.splitlines():
        if line.startswith("## [") and "]" in line:
            if current_ref is not None:
                chunks[current_ref] = "\n".join(current_lines).strip()
            current_ref = line.split("[", 1)[1].split("]", 1)[0]
            current_lines = [line]
            continue
        if current_ref is not None:
            current_lines.append(line)

    if current_ref is not None:
        chunks[current_ref] = "\n".join(current_lines).strip()
    return chunks


def _title_from_ref(ref: str) -> str:
    parts = ref.split(":")
    if len(parts) >= 3 and parts[0] in _RENDERABLE_RAW_TYPES:
        return re.sub(r"\.md$", "", parts[1])
    return ref


def _title_from_path(path: str | None) -> str | None:
    if not path:
        return None
    stem = Path(path).stem
    if stem.upper() == "SKILL":
        return None
    return stem


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return parsed


def _validate_positive_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    if limit > 100:
        raise ValueError(f"limit must be between 1 and 100 (got {limit})")
    return limit


def _extract_path(chunk: str) -> str | None:
    patterns = [
        r"^\s*read\s+(.+)$",
        r"^\*\*Read\*\*:\s*read\s+(.+)$",
        r"^\*\*Path\*\*:\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, chunk, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _extract_source(chunk: str) -> str | None:
    match = re.search(r"^\*\*Source\*\*:\s*(.+)$", chunk, re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_skill_title(chunk: str) -> str | None:
    match = re.search(r"^# Skill:\s*(.+)$", chunk, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r"^name:\s*(.+)$", chunk, re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_heading(chunk: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", chunk, re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_useful_description(chunk: str) -> str | None:
    for pattern in _DESCRIPTION_PATTERNS:
        match = re.search(pattern, chunk, re.IGNORECASE | re.MULTILINE)
        if not match:
            continue
        text = match.group(1).strip() if match.lastindex else match.group(0).strip()
        text = _ANSI_ESCAPE_RE.sub("", text)
        if text and not text.lower().startswith("skill:"):
            return text
    for raw_line in chunk.replace("\\n", "\n").splitlines():
        line = _ANSI_ESCAPE_RE.sub("", raw_line).strip()
        if not line:
            continue
        lowered = line.lower()
        if (
            line.startswith("<!--")
            or lowered.startswith("## [")
            or lowered.startswith("read ")
            or lowered in {"---", "..."}
            or lowered.startswith("# skill:")
            or lowered.startswith("**source**:")
            or lowered.startswith("source:")
            or lowered.startswith("name:")
            or lowered.startswith("origin:")
        ):
            continue
        if lowered.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value:
                return value
        return line
    return None


def _infer_source_from_path(path: str | None) -> str | None:
    if not path:
        return None
    source_path = path.lower()
    if "/.pi/agent/skills/" in source_path:
        return "pi-agent-skills"
    if "/.claude/skills/" in source_path:
        return "claude-skills"
    if "/.codex/skills/" in source_path:
        return "codex-skills"
    if "/.agents/skills/anthropic-skills/" in source_path:
        return "anthropic-skills"
    if "examen_grado" in source_path:
        return "examen_grado"
    return None


def _looks_like_metadata(chunk: str) -> bool:
    lowered = chunk.lower()
    return "administrative segment metadata" in lowered or "not an executable skill" in lowered


def _metadata_message(chunk: str, raw_type: str) -> str:
    heading = _extract_heading(chunk)
    if heading:
        return f"{heading}. Administrative metadata only; not an executable skill."
    return f"{raw_type} result is administrative metadata only; not an executable skill."


def _looks_like_json_payload(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


if __name__ == "__main__":
    raise SystemExit(cli())
