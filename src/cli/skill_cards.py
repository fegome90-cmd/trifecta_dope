"""
Reference skill card renderers for repo-side CLI usage.

Generates cards with full skill information for agent and human consumption.
Supports 3 output styles: rich (Panel), compact (Table), plain (text).

Important:
- Promoted runtime authority lives under /scripts.
- This module is intentionally reference-only for repo-side callers.

Design System:
- 4px grid spacing
- Typography hierarchy (headline 600, body 400, label 500)
- Contrast hierarchy (foreground → secondary → muted → faint)
- Borders-only depth strategy (clean, technical)

Author: Trifecta Team
Date: 2026-03-19
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from src.application.skill_card_view_model import SkillCardViewModel

from typing import IO, Literal

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS (4px grid system)
# ═══════════════════════════════════════════════════════════════════════════════

# Spacing (4px base, expressed in chars for terminal)
SPACE_1 = 1  # micro (4px)
SPACE_2 = 2  # tight (8px)
SPACE_3 = 3  # standard (12px)
SPACE_4 = 4  # comfortable (16px)

# Typography weights (conceptual for terminal)
WEIGHT_HEADLINE = "bold"  # skill name
WEIGHT_BODY = ""  # description
WEIGHT_LABEL = ""  # metadata

# Contrast hierarchy (4 levels)
COLOR_FOREGROUND = "white"
COLOR_SECONDARY = "cyan"
COLOR_MUTED = "dim"
COLOR_FAINT = "grey50"

# Border strategy: borders-only (clean, technical)
BORDER_STYLE = "blue"
BORDER_SUBTLE = "dim blue"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════════

OutputStyle = Literal["rich", "compact", "plain"]

_SKILL_HUB_INTRO_BANNER = "=== Skill Hub ==="
_SKILL_HUB_SENTENCE_GUIDANCE = (
    "Tip: write your query as a sentence query so the search intent is explicit."
)


def render_skill_hub_intro(
    *,
    query_hint: str | None = None,
    file: IO[str] | None = None,
) -> None:
    """Reference intro renderer for repo-side callers (non-runtime authority)."""
    output = file or sys.stdout
    lines = [
        _SKILL_HUB_INTRO_BANNER,
        _SKILL_HUB_SENTENCE_GUIDANCE,
    ]
    if query_hint:
        lines.append(f"Query: {query_hint}")
    print("\n".join(lines), file=output)


# ═══════════════════════════════════════════════════════════════════════════════
# RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def render_card(
    card: SkillCardViewModel,
    style: OutputStyle = "plain",
    file: IO[str] | None = None,
) -> None:
    """
    Render skill card with design system compliance.

    Args:
        card: Skill card data
        style: Output style - rich (Panel), compact (Table), plain (text)
        file: Output file handle (default: sys.stdout)

    Styles:
    - rich: Full Panel with visual hierarchy (default for humans in TTY)
    - compact: Single-line table row (for dense listings)
    - plain: Text-only (default for agents, pipes, redirects)
    """
    # Note: TTY detection removed - caller should pass correct style

    if style == "rich":
        _render_rich(card, file)
    elif style == "compact":
        _render_compact(card, file)
    else:
        _render_plain(card, file)


def _render_rich(card: SkillCardViewModel, file: IO[str] | None = None) -> None:
    """
    Rich Panel card with full visual hierarchy.

    Anatomy:
    ╭─ workorder-execution-base ── pi-agent ── █████░░░░╮
    │                                              │
    │ Use when executing multi-phase...            │
    │                                              │
    │ ▸ triggers: git-worktree, verification       │
    │                                              │
    │ $ read /path/to/SKILL.md                     │
    ╰──────────────────────────────────────────────╯
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich import box
    except ImportError:
        # Fallback to plain if rich not available
        _render_plain(card, file)
        return

    console = Console(file=file, force_terminal=True)

    # ── Header: name + source badge + relevance ──
    header = Text()
    header.append(card.name, style=f"{WEIGHT_HEADLINE} {COLOR_SECONDARY}")
    header.append("  ", style="reset")
    header.append(card.source, style=COLOR_MUTED)

    if card.authority_state == "degraded":
        header.append("  ", style="reset")
        header.append("[DEGRADED]", style="bold red")

    if card.relevance > 0:
        header.append("  ", style="reset")
        # Relevance as visual bar: ████░░░░
        filled = int(card.relevance * 5)
        bar = "█" * filled + "░" * (5 - filled)
        header.append(bar, style=COLOR_MUTED)

    # ── Body: description + triggers + command ──
    body = Text()

    # Description
    body.append(card.description, style=COLOR_FOREGROUND)

    # Triggers (if present)
    if card.triggers:
        body.append("\n\n")
        triggers_line = Text()
        triggers_line.append("▸ triggers: ", style=COLOR_MUTED)
        triggers_line.append(", ".join(card.triggers[:3]), style=COLOR_FAINT)
        body.append(triggers_line)

    # Command (actionable, prominent)
    body.append("\n\n")
    cmd = Text()
    cmd.append("read ", style=COLOR_SECONDARY)
    cmd.append(card.path, style=f"underline {COLOR_FAINT}")
    body.append(cmd)

    # ── Panel assembly ──
    panel = Panel(
        body,
        title=header,
        border_style=BORDER_SUBTLE,
        box=box.ROUNDED,
        padding=(SPACE_1, SPACE_2),
        expand=False,
    )

    console.print(panel)


def _render_compact(card: SkillCardViewModel, file: IO[str] | None = None) -> None:
    """
    Compact table row for dense listings.

    Format:
    workorder-execution  pi-agent  87%  Use when executing multi-phase...
    """
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        _render_plain(card, file)
        return

    console = Console(file=file, force_terminal=True)

    table = Table(show_header=False, box=None, padding=(0, SPACE_1))
    table.add_column("Name", style=f"{WEIGHT_HEADLINE} {COLOR_SECONDARY}", width=24)
    table.add_column("Source", style=COLOR_MUTED, width=12)
    table.add_column("Rel", style=COLOR_MUTED, width=5)
    table.add_column("Description", style=COLOR_FOREGROUND)

    # Truncate description to fit
    desc = card.description[:60] + "..." if len(card.description) > 60 else card.description

    rel = f"{int(card.relevance * 100)}%" if card.relevance > 0 else "-"

    name_display = card.name[:24]
    if card.authority_state == "degraded":
        name_display = f"{card.name[:13]} [DEGRADED]"

    table.add_row(name_display, card.source[:12], rel, desc)
    console.print(table)


def _render_plain(card: SkillCardViewModel, file: IO[str] | None = None) -> None:
    """
    Plain text format for agent parsing.

    No Rich formatting - pure text for copy-paste.
    Designed for stable agent consumption.

    Format:
        # Skill: <name>
        read <path>
        Source: <source>

        <description>

        ---
    """
    output = file or sys.stdout

    lines = [
        f"# Skill: {card.name}",
        f"read {card.path}",
        f"Source: {card.source}",
    ]

    if card.authority_state == "degraded":
        lines.append("Status: DEGRADED")

    lines.append("")
    lines.append(card.description)

    if card.triggers:
        lines.append("")
        lines.append(f"Triggers: {', '.join(card.triggers)}")

    lines.append("")
    lines.append("---")

    print("\n".join(lines), file=output)


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_cards(
    cards: list[SkillCardViewModel],
    style: OutputStyle = "plain",
    title: str | None = None,
    file: IO[str] | None = None,
) -> None:
    """Render multiple cards with optional header."""
    output = file or sys.stdout

    if title and style == "rich":
        try:
            from rich.console import Console
            console = Console(file=output, force_terminal=True)
            console.print()
            console.rule(f"[bold]{title}[/bold]", style=BORDER_STYLE)
            console.print()
        except ImportError:
            pass

    for i, card in enumerate(cards):
        render_card(card, style, output)
        if style == "rich" and i < len(cards) - 1:
            try:
                from rich.console import Console
                console = Console(file=output, force_terminal=True)
                console.print()
            except ImportError:
                print(file=output)


# ═══════════════════════════════════════════════════════════════════════════════
# PARSING UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def parse_skill_from_chunk(chunk_text: str, chunk_id: str) -> SkillCardViewModel | None:
    """Parse skill metadata from a context chunk.

    .. deprecated::
        Transitional shim — will be removed in a future cleanup phase.
        Relies on regex over chunk_text as secondary authority, which is prohibited as
        primary source of truth. Use ``build_view_model(ClassifiedResult)`` in
        ``scripts/skill_hub_cards_core.py`` as the canonical path instead.

    Supports multiple formats:
    - New: "read /path/to/SKILL.md" on first line
    - Legacy: "**Path**: /path/to/SKILL.md"
    - Oldest: "**Read**: read /path/to/SKILL.md"

    Args:
        chunk_text: Full text of the skill chunk
        chunk_id: Chunk ID (e.g., "skill:workorder-execution-base:abc123")

    Returns:
        SkillCardViewModel if parseable, None otherwise
    """
    # Extract name from chunk_id
    # Format: skill:<name>:<fingerprint> or skill:<name>
    id_parts = chunk_id.split(":")
    if len(id_parts) < 2:
        return None
    name = id_parts[1]

    # Try new format: read /path (first occurrence)
    path_match = re.search(r"^\s*read\s+(.+)$", chunk_text, re.MULTILINE)

    # Fallback: **Read**: read /path
    if not path_match:
        path_match = re.search(r"^\*\*Read\*\*:\s*read\s+(.+)$", chunk_text, re.MULTILINE)

    # Fallback: **Path**: /path
    if not path_match:
        path_match = re.search(r"^\*\*Path\*\*:\s*(.+)$", chunk_text, re.MULTILINE)

    if not path_match:
        return None

    path = path_match.group(1).strip()

    # Extract source
    source_match = re.search(r"^\*\*Source\*\*:\s*(.+)$", chunk_text, re.MULTILINE)
    source = source_match.group(1).strip() if source_match else "unknown"

    # Extract description (after managed block markers or after Source/Search Hints)
    # Look for "Use when" pattern which is the standard description start
    desc_match = re.search(
        r"(?:Use when|Use for)[^\n]+(?:\n[^\n]+)*",
        chunk_text,
        re.MULTILINE
    )
    description = desc_match.group(0).strip() if desc_match else ""

    # Extract search hints if present
    hints_match = re.search(r"^\*\*Search Hints\*\*:\s*(.+)$", chunk_text, re.MULTILINE)
    search_hints = hints_match.group(1).strip() if hints_match else None

    return SkillCardViewModel(
        id=name,
        name=name,
        path=path,
        source=source,
        description=description,
        search_hints=search_hints,
        authority_state="healthy"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Demo: skill cards rendering."""
    sample_cards = [
        SkillCardViewModel(
            id="workorder-execution-base",
            name="workorder-execution-base",
            path="/Users/felipe/.pi/agent/skills/workorder-execution-base/SKILL.md",
            source="pi-agent",
            description="Use when executing multi-phase remediation or refactor plans split into WorkOrders, especially with isolated git worktrees, strict verification gates.",
            triggers=("git-worktree", "verification", "gates"),
            relevance=0.92,
            authority_state="healthy"
        ),
        SkillCardViewModel(
            id="git-worktree-curated",
            name="git-worktree-curated",
            path="/Users/felipe/.pi/agent/skills/git-worktree-curated/SKILL.md",
            source="pi-agent",
            description="Use when parallel branch work, isolated environments, or Work Order execution require creating, listing, cleaning, or repairing git worktrees safely.",
            triggers=("parallel", "isolation", "worktree"),
            relevance=0.85,
            authority_state="degraded"
        ),
        SkillCardViewModel(
            id="python-cli-patterns",
            name="python-cli-patterns",
            path="/Users/felipe/.pi/agent/skills/python-cli-patterns/SKILL.md",
            source="pi-agent",
            description="Use for Python CLI apps: Typer, Click, argparse, Rich, terminal UX. Do NOT use for pytest or general Python idioms.",
            triggers=("cli", "typer", "rich"),
            relevance=0.78,
            authority_state="healthy"
        ),
    ]

    import argparse
    parser = argparse.ArgumentParser(description="Skill Cards Demo")
    parser.add_argument("--style", "-s", choices=["rich", "compact", "plain"],
                       default="rich", help="Output style")
    parser.add_argument("--limit", "-n", type=int, default=3, help="Max cards")
    args = parser.parse_args()

    render_cards(sample_cards[:args.limit], style=args.style, title="Skill Search Results")


if __name__ == "__main__":
    main()
