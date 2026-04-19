from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

from skill_hub_runtime_ux import (
    RuntimeSkillCard,
    render_cards_plain,
    render_cards_rich,
    render_non_renderable_message,
)

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


@dataclass(frozen=True)
class RawSearchHit:
    ref: str
    raw_type: str
    title: str
    score: float
    authority_state: str = "healthy"


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
    authority_state: str = "healthy"


@dataclass(frozen=True)
class ClassifiedResult:
    kind: str
    normalized: NormalizedResult
    reason: str



@dataclass(frozen=True)
class RenderPlan:
    outcome_kind: str
    exit_code: int
    cards: list[RuntimeSkillCard]
    message: str
    classified_results: list[ClassifiedResult]


class SearchRuntimeError(RuntimeError):
    pass


class GetRuntimeError(RuntimeError):
    pass


class SearchParseError(RuntimeError):
    pass


# Backward-compat alias used by parity tests and legacy adapters.
SkillCardViewModel = RuntimeSkillCard


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

    hits = payload.get("hits", [])
    if not isinstance(hits, list):
        raise SearchParseError("invalid hits list in search JSON payload")

    authority_state = payload.get("authority_state", "healthy")

    parsed: list[RawSearchHit] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        ref = str(hit.get("ref", "")).strip()
        if not ref:
            continue
        raw_type = ref.split(":", 1)[0]
        parsed.append(
            RawSearchHit(
                ref=ref,
                raw_type=raw_type,
                title=_title_from_ref(ref),
                score=float(hit.get("score", 0.0) or 0.0),
                authority_state=str(authority_state),
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
        score = float(score_match.group(1)) if score_match else 0.0
        results.append(RawSearchHit(ref=ref, raw_type=raw_type, title=title, score=score, authority_state="healthy"))
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
            authority_state=hit.authority_state,
        )

    path = _extract_path(clean_chunk)
    explicit_title = _extract_skill_title(clean_chunk)
    visible_title = (
        explicit_title or _title_from_ref(hit.ref) or _title_from_path(path) or hit.title
    )
    stable_id = slugify(explicit_title or _title_from_ref(hit.ref) or _title_from_path(path) or hit.title)
    source = _extract_source(clean_chunk) or _extract_registered_via(clean_chunk) or _infer_source_from_path(path)
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
        authority_state=hit.authority_state,
    )


def classify_result(normalized: NormalizedResult) -> ClassifiedResult:
    if normalized.raw_type in _METADATA_RAW_TYPES or normalized.metadata_message:
        return ClassifiedResult(
            kind="metadata_only",
            normalized=normalized,
            reason=normalized.metadata_reason
            or "administrative metadata is not renderable as a skill card",
        )

    if normalized.raw_type not in _RENDERABLE_RAW_TYPES:
        return ClassifiedResult(
            kind="unsupported",
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
            kind="renderable_skill",
            normalized=normalized,
            reason="sufficient trusted fields available for skill card rendering",
        )

    return ClassifiedResult(
        kind="unsupported",
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
    hits = parse_search_output(raw_search_output, strict_json=strict_json)
    if not hits:
        return RenderPlan(
            outcome_kind="empty",
            exit_code=EXIT_EMPTY,
            cards=[],
            message="No search hits found.",
            classified_results=[],
        )

    classified_results = [
        classify_result(normalize_result(hit, chunk_texts.get(hit.ref, ""))) for hit in hits[:limit]
    ]
    cards: list[SkillCardViewModel] = [
        card
        for result in classified_results
        if result.kind == "renderable_skill"
        if (card := build_view_model(result)) is not None
    ]

    if cards:
        return RenderPlan(
            outcome_kind="renderable_skill",
            exit_code=EXIT_RENDERABLE,
            cards=cards,
            message="",
            classified_results=classified_results,
        )

    if classified_results and all(result.kind == "metadata_only" for result in classified_results):
        return RenderPlan(
            outcome_kind="metadata_only",
            exit_code=EXIT_NON_RENDERABLE,
            cards=[],
            message="Administrative metadata found, but it is not renderable as a skill card.",
            classified_results=classified_results,
        )

    return RenderPlan(
        outcome_kind="unsupported",
        exit_code=EXIT_NON_RENDERABLE,
        cards=[],
        message="Search returned hits, but they could not be promoted safely to a skill card.",
        classified_results=classified_results,
    )


def render_plain(plan: RenderPlan) -> str:
    if plan.outcome_kind == "renderable_skill":
        return render_cards_plain(plan.cards).strip()
    return render_non_renderable_message(outcome_kind=plan.outcome_kind, message=plan.message)


def render_rich(plan: RenderPlan, *, title: str | None = None) -> str:
    if plan.outcome_kind == "renderable_skill":
        return render_cards_rich(plan.cards, title=title).strip()

    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
    except ImportError:
        return render_plain(plan)

    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=100)

    style = "yellow" if plan.outcome_kind == "metadata_only" else "red"
    title = "Metadata only" if plan.outcome_kind == "metadata_only" else "Non-renderable result"
    console.print(Panel(plan.message, title=title, border_style=style, box=box.ROUNDED))
    return buffer.getvalue().strip()


def run_search(query: str, limit: int, *, segment_path: Path | None = None) -> str:
    resolved = segment_path or DEFAULT_SEGMENT_PATH
    env = os.environ.copy()
    env.update({"TRIFECTA_LINT": "1", "TRIFECTA_NO_TELEMETRY": "1"})
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
    )
    if result.returncode != 0:
        raise SearchRuntimeError(
            result.stderr.strip() or result.stdout.strip() or "unknown search error"
        )
    return result.stdout


def run_get(chunk_ids: Iterable[str], *, segment_path: Path | None = None) -> dict[str, str]:
    resolved = segment_path or DEFAULT_SEGMENT_PATH
    refs = [chunk_id for chunk_id in chunk_ids if chunk_id]
    if not refs:
        return {}

    env = os.environ.copy()
    env.update({"TRIFECTA_LINT": "1", "TRIFECTA_NO_TELEMETRY": "1"})
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
    )
    if result.returncode != 0:
        raise GetRuntimeError(result.stderr.strip() or result.stdout.strip() or "unknown get error")
    return _parse_get_output(result.stdout)


def output_json(plan: RenderPlan) -> str:
    payload = {
        "outcome_kind": plan.outcome_kind,
        "exit_code": plan.exit_code,
        "message": plan.message,
        "cards": [card.__dict__ for card in plan.cards],
        "classified_results": [
            {
                "kind": item.kind,
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
        "--limit", "-l", type=int, default=5, help="Max cards / hits to evaluate (default: 5)"
    )
    parser.add_argument(
        "--segment",
        type=Path,
        default=None,
        help="Path to skills-hub segment (default: ~/.trifecta/segments/skills-hub)",
    )
    parser.add_argument(
        "--style",
        choices=["auto", "plain", "rich"],
        default="auto",
        help="Output style (default: auto; rich on TTY, plain otherwise)",
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
    segment_path = args.segment

    try:
        raw_search_output = _load_search_payload(args, segment_path=segment_path)
        strict_json = args.stdin_search_output and _looks_like_json_payload(raw_search_output)
        hits = parse_search_output(raw_search_output, strict_json=strict_json)
        chunk_texts = run_get((hit.ref for hit in hits), segment_path=segment_path)
        plan = build_render_plan(
            raw_search_output, chunk_texts, limit=args.limit, strict_json=strict_json
        )
    except (SearchRuntimeError, GetRuntimeError, SearchParseError) as exc:
        print(f"skill-hub-cards: {exc}", file=sys.stderr)
        return EXIT_ERROR

    title = f"SKILL HUB: {args.query}" if args.query else "SKILL HUB"
    stream = sys.stdout if plan.outcome_kind == "renderable_skill" else sys.stderr
    rendered = _select_renderer(
        plan, use_json=args.json, style=args.style, title=title, output_stream=stream
    )
    if rendered:
        print(rendered, file=stream)
    return plan.exit_code


def _stream_is_tty(stream: io.TextIOBase) -> bool:
    is_tty = getattr(stream, "isatty", None)
    return callable(is_tty) and bool(is_tty())


def _resolve_style(style: str, output_stream: io.TextIOBase) -> str:
    if style != "auto":
        return style
    return "rich" if _stream_is_tty(output_stream) else "plain"


def _select_renderer(
    plan: RenderPlan,
    *,
    use_json: bool,
    style: str,
    title: str | None = None,
    output_stream: io.TextIOBase,
) -> str:
    if use_json:
        return output_json(plan)

    resolved_style = _resolve_style(style, output_stream)

    if plan.outcome_kind != "renderable_skill":
        # Let the legacy renderers handle administrative/error frames 
        # until Phase 6 cleanup formally refactors non-renderable output
        if resolved_style == "rich":
            return render_rich(plan)
        return render_plain(plan)

    if resolved_style == "rich":
        return render_rich(plan, title=title)
    return render_plain(plan)


def _load_search_payload(args: argparse.Namespace, *, segment_path: Path | None = None) -> str:
    if args.stdin_search_output:
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
def build_view_model(result: ClassifiedResult) -> RuntimeSkillCard | None:
    """Adapter function: ClassifiedResult -> SkillCardViewModel.
    
    ClassifiedResult is the chosen authoritative border because it is
    the final stable logical structure resulting from the pipeline evaluation
    and normalization, before grouping/rendering logic starts.
    """
    if result.kind != "renderable_skill":
        return None
        
    normalized = result.normalized
    if not normalized.stable_id or not normalized.visible_title:
        return None
        
    # Strictly map authority state, fallback string mapping if necessary but no inference.
    auth_state: Literal["healthy", "degraded"] = "healthy"
    if normalized.authority_state == "degraded":
        auth_state = "degraded"
        
    return RuntimeSkillCard(
        id=normalized.stable_id,
        name=normalized.visible_title,
        path=normalized.path or "unknown",
        source=normalized.source or "unknown",
        description=normalized.description or "No description",
        authority_state=auth_state,
        relevance=normalized.score,
    )


def _title_from_ref(ref: str) -> str:
    parts = ref.split(":")
    if len(parts) >= 3 and parts[0] in _RENDERABLE_RAW_TYPES:
        return re.sub(r"\.md$", "", parts[1])
    return ref


def _title_from_path(path: str | None) -> str | None:
    if not path:
        return None
    return Path(path).stem


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


def _extract_registered_via(chunk: str) -> str | None:
    match = re.search(r"^\*\*Registered Via\*\*:\s*(.+)$", chunk, re.MULTILINE)
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


def _score_bar(score: float) -> str:
    filled = max(0, min(5, int(round(min(score / 5.0, 1.0) * 5))))
    return "●" * filled + "○" * (5 - filled)


def _looks_like_json_payload(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


if __name__ == "__main__":
    raise SystemExit(cli())
