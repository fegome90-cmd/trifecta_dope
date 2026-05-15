from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from typing import IO, Iterable


ANSI_RESET = "\033[0m"
ANSI_BRIGHT_WHITE = "\033[1;97m"
SKILL_HUB_INTRO_BANNER = "=== Skill Hub ==="
SKILL_HUB_HERO_BANNER = (
    "███████╗██╗  ██╗██╗██╗     ██╗     ███████╗",
    "██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝",
    "███████╗█████╔╝ ██║██║     ██║     ███████╗",
    "╚════██║██╔═██╗ ██║██║     ██║     ╚════██║",
    "███████║██║  ██╗██║███████╗███████╗███████║",
    "╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝",
)
SKILL_HUB_SENTENCE_GUIDANCE = (
    "Tip: write your query as a sentence query so the search intent is explicit."
)


@dataclass(frozen=True)
class RuntimeSkillCard:
    id: str
    name: str
    path: str
    source: str
    description: str
    authority_state: str = "healthy"
    fidelity_level: str = "full"
    compact_flag: bool = False
    search_hints: str | None = None
    triggers: tuple[str, ...] = ()
    relevance: float = 0.0
    synthetic: bool = False

    def __post_init__(self) -> None:
        if self.id is None:
            raise ValueError("id must be provided, not None")
        if self.name is None:
            raise ValueError("name must be provided, not None")
        if self.authority_state not in ("healthy", "degraded"):
            raise ValueError(
                f"authority_state must be 'healthy' or 'degraded', got {self.authority_state!r}"
            )


def _is_tty(file: IO[str]) -> bool:
    is_tty = getattr(file, "isatty", None)
    return callable(is_tty) and is_tty()


def _use_color() -> bool:
    return not os.environ.get("NO_COLOR")


def _banner_lines(*, rich: bool, colorize: bool) -> list[str]:
    if not rich:
        return [SKILL_HUB_INTRO_BANNER]
    if colorize:
        return [f"{ANSI_BRIGHT_WHITE}{line}{ANSI_RESET}" for line in SKILL_HUB_HERO_BANNER]
    return list(SKILL_HUB_HERO_BANNER)


def render_intro(*, query_hint: str | None = None, rich: bool = False, colorize: bool | None = None) -> str:
    resolved_colorize = _use_color() if colorize is None else colorize
    lines = _banner_lines(rich=rich, colorize=resolved_colorize)
    if rich:
        lines.append("")
    lines.append(SKILL_HUB_SENTENCE_GUIDANCE)
    if query_hint:
        lines.append(f"Query: {query_hint}")
    return "\n".join(lines)


def emit_intro(*, query_hint: str | None = None, file: IO[str] | None = None) -> None:
    output = file or sys.stdout
    rich = _is_tty(output)
    print(render_intro(query_hint=query_hint, rich=rich, colorize=_use_color()), file=output)


def render_error_card(
    *,
    error_code: str,
    error_class: str,
    cause: str,
    next_steps: list[str],
    verify_cmd: str,
) -> str:
    steps = "\n  ".join(next_steps)
    return (
        f"TRIFECTA_ERROR_CODE: {error_code}\n"
        f"❌ TRIFECTA_ERROR: {error_code}\n"
        f"CLASS: {error_class}\n"
        f"CAUSE: {cause}\n\n"
        "NEXT_STEPS:\n"
        f"  {steps}\n\n"
        "VERIFY:\n"
        f"  {verify_cmd}\n"
    )


def emit_error_card(
    *,
    error_code: str,
    error_class: str,
    cause: str,
    next_steps: list[str],
    verify_cmd: str,
    file: IO[str] | None = None,
) -> None:
    output = file or sys.stderr
    print(
        render_error_card(
            error_code=error_code,
            error_class=error_class,
            cause=cause,
            next_steps=next_steps,
            verify_cmd=verify_cmd,
        ),
        file=output,
        end="",
    )


def render_cards_plain(cards: Iterable[RuntimeSkillCard]) -> str:
    blocks: list[str] = []
    for card in cards:
        description = card.description if card.description else "Description unavailable"
        lines = [
            f"# Skill: {card.name}{' [synthetic]' if card.synthetic else ''}",
            f"read {card.path}",
            f"Source: {card.source}",
        ]
        if card.authority_state == "degraded":
            lines.append("Status: DEGRADED")
        lines.extend(["", description])
        blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)


def render_cards_rich(
    cards: Iterable[RuntimeSkillCard], *, title: str | None = None, width: int = 100
) -> str:
    cards_list = list(cards)
    if not cards_list:
        return ""
    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
    except ImportError:
        return render_cards_plain(cards_list)

    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=width)

    if title:
        console.rule(f"[bold]{title}[/bold]", style="dim blue")

    for idx, card in enumerate(cards_list):
        description = card.description if card.description else "Description unavailable"
        header = Text()
        header.append(card.name, style="bold cyan")
        header.append("  ", style="reset")
        header.append(card.source, style="dim")
        if card.authority_state == "degraded":
            header.append("  [DEGRADED]", style="bold red")
        if card.synthetic:
            header.append("  [SYNTHETIC]", style="bold yellow")

        body = Text()
        body.append(description, style="white")
        body.append("\n\n")
        body.append("read ", style="cyan")
        body.append(card.path, style="underline grey50")

        panel = Panel(
            body,
            title=header,
            border_style="dim blue",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=False,
        )
        console.print(panel)
        if idx < len(cards_list) - 1:
            console.print()

    return buffer.getvalue().strip()


def render_non_renderable_message(*, outcome_kind: str, message: str) -> str:
    title_map = {
        "metadata_only": "# No valid skill cards",
        "unsupported": "# No valid skill cards",
        "empty": "# No search hits found",
    }
    title = title_map.get(outcome_kind, "# skill-hub-cards")
    return f"{title}\n{message}".strip()
