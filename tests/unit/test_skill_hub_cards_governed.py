from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = REPO_ROOT / "scripts" / "skill_hub_cards_core.py"
HELPER_PATH = REPO_ROOT / "scripts" / "skill-hub-cards"
SHIM_PATH = REPO_ROOT / "scripts" / "skill_hub_cards.py"


def load_module() -> Any:
    assert CORE_PATH.exists(), f"missing governed core module: {CORE_PATH}"
    spec = importlib.util.spec_from_file_location("skill_hub_cards_core_mod", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load skill_hub_cards_core.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["skill_hub_cards_core_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def search_payload(*hits: dict[str, Any]) -> str:
    return json.dumps({"hits": list(hits)})


def test_query_with_skill_result_renders_card_and_exit_zero() -> None:
    mod = load_module()
    payload = search_payload({"ref": "skill:test-driven-development:abc123", "score": 1.5})
    chunks = {
        "skill:test-driven-development:abc123": (
            "## [skill:test-driven-development:abc123] test-driven-development\n"
            "read /Users/felipe_gonzalez/.codex/skills/test-driven-development/SKILL.md\n"
            "# Skill: test-driven-development\n"
            "**Source**: codex-skills\n"
            "Use when implementing any feature or bugfix, before writing implementation code.\n"
        )
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)

    assert plan.outcome_kind == "renderable_skill"
    assert plan.exit_code == 0
    assert [card.id for card in plan.cards] == ["test-driven-development"]
    assert "before writing implementation code" in mod.render_plain(plan)


def test_repo_result_promotes_only_when_confidence_is_sufficient() -> None:
    mod = load_module()
    payload = search_payload({"ref": "repo:checkpoint-card.md:3fa52a12a1", "score": 1.5})
    chunks = {
        "repo:checkpoint-card.md:3fa52a12a1": (
            "## [repo:checkpoint-card.md:3fa52a12a1] checkpoint-card.md\n"
            "<!-- managed-by:indexing-skills-safely:start -->\n"
            "read /Users/felipe_gonzalez/.pi/agent/skills/checkpoint-card/SKILL.md\n"
            "# Skill: checkpoint-card\n"
            "**Source**: pi-agent-skills\n"
            "Use for saving session state as checkpoint card for agent handoff.\n"
            "<!-- managed-by:indexing-skills-safely:end -->\n"
        )
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)

    assert plan.outcome_kind == "renderable_skill"
    assert plan.exit_code == 0
    assert [card.id for card in plan.cards] == ["checkpoint-card"]
    assert plan.cards[0].path.endswith("/checkpoint-card/SKILL.md")


def test_repo_result_fails_closed_when_confidence_is_insufficient() -> None:
    mod = load_module()
    payload = search_payload({"ref": "repo:mystery-card.md:deadbeef", "score": 1.5})
    chunks = {
        "repo:mystery-card.md:deadbeef": (
            "## [repo:mystery-card.md:deadbeef] mystery-card.md\n"
            "Some repository document that mentions a skill but has no read path.\n"
        )
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)

    assert plan.outcome_kind == "unsupported"
    assert plan.exit_code == 3
    assert not plan.cards
    assert "could not be promoted safely" in plan.message.lower()


def test_metadata_only_results_do_not_claim_no_skills_found() -> None:
    mod = load_module()
    payload = search_payload(
        {"ref": "prime:efbc132df7", "score": 1.5},
        {"ref": "session:97344fc272", "score": 1.0},
    )
    chunks = {
        "prime:efbc132df7": (
            "## [prime:efbc132df7] prime_skills-hub.md\n"
            "# Segment Metadata — Prime Skills Hub\n"
            "Administrative segment metadata.\n"
            "Not an executable skill.\n"
        ),
        "session:97344fc272": (
            "## [session:97344fc272] session_skills-hub.md\n"
            "# Segment Metadata — Session Skills Hub\n"
            "Administrative segment metadata.\n"
            "Not an executable skill.\n"
        ),
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)
    plain = mod.render_plain(plan)

    assert plan.outcome_kind == "metadata_only"
    assert plan.exit_code == 3
    assert "administrative metadata" in plain.lower()
    assert "no skills found" not in plain.lower()


def test_empty_results_have_dedicated_exit_code() -> None:
    mod = load_module()

    plan = mod.build_render_plan(search_payload(), {}, limit=5)

    assert plan.outcome_kind == "empty"
    assert plan.exit_code == 4
    assert "no search hits found" in plan.message.lower()


def test_plain_and_rich_render_share_same_classification() -> None:
    mod = load_module()
    payload = search_payload({"ref": "repo:tdd-coach.md:98be042492", "score": 1.5})
    chunks = {
        "repo:tdd-coach.md:98be042492": (
            "## [repo:tdd-coach.md:98be042492] tdd-coach.md\n"
            "read /Users/felipe_gonzalez/.pi/agent/skills/tdd-coach/SKILL.md\n"
            "# Skill: tdd-coach\n"
            "**Source**: pi-agent-skills\n"
            "Use for TDD process coaching: RED-GREEN-REFACTOR cycle.\n"
        )
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)
    plain = mod.render_plain(plan)
    rich = strip_ansi(mod.render_rich(plan))

    assert plan.outcome_kind == "renderable_skill"
    assert plan.exit_code == 0
    assert "tdd-coach" in plain
    assert "tdd-coach" in rich
    assert "RED-GREEN-REFACTOR" in plain
    assert "RED-GREEN-REFACTOR" in rich


def test_governed_helper_accepts_style_plain_and_rich_flags() -> None:
    assert HELPER_PATH.exists(), f"missing governed helper: {HELPER_PATH}"
    plain_help = subprocess.run(
        [sys.executable, str(HELPER_PATH), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert plain_help.returncode == 0
    help_text = plain_help.stdout + plain_help.stderr
    assert "--style" in help_text
    assert "plain" in help_text
    assert "rich" in help_text


def test_deprecated_python_entrypoint_is_only_a_shim() -> None:
    assert SHIM_PATH.exists(), f"missing deprecated shim: {SHIM_PATH}"
    text = SHIM_PATH.read_text()

    assert "deprecated" in text.lower()
    assert "skill-hub-cards" in text
    assert "parse_search_output" not in text
    assert "normalize_result" not in text
    assert "classify_result" not in text
    assert "Panel(" not in text


def test_mixed_renderable_and_metadata_only_batch_is_success() -> None:
    mod = load_module()
    payload = search_payload(
        {"ref": "prime:efbc132df7", "score": 1.5},
        {"ref": "repo:checkpoint-card.md:3fa52a12a1", "score": 1.2},
    )
    chunks = {
        "prime:efbc132df7": (
            "## [prime:efbc132df7] prime_skills-hub.md\n"
            "# Segment Metadata — Prime Skills Hub\n"
            "Administrative segment metadata.\n"
            "Not an executable skill.\n"
        ),
        "repo:checkpoint-card.md:3fa52a12a1": (
            "## [repo:checkpoint-card.md:3fa52a12a1] checkpoint-card.md\n"
            "read /Users/felipe_gonzalez/.pi/agent/skills/checkpoint-card/SKILL.md\n"
            "# Skill: checkpoint-card\n"
            "**Source**: pi-agent-skills\n"
            "Use for saving session state as checkpoint card for agent handoff.\n"
        ),
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)

    assert plan.outcome_kind == "renderable_skill"
    assert plan.exit_code == 0
    assert [card.id for card in plan.cards] == ["checkpoint-card"]


def test_mixed_unsupported_and_metadata_only_batch_is_non_renderable() -> None:
    mod = load_module()
    payload = search_payload(
        {"ref": "repo:mystery-card.md:deadbeef", "score": 1.5},
        {"ref": "session:97344fc272", "score": 1.0},
    )
    chunks = {
        "repo:mystery-card.md:deadbeef": (
            "## [repo:mystery-card.md:deadbeef] mystery-card.md\n"
            "Repository prose only, without trusted card fields.\n"
        ),
        "session:97344fc272": (
            "## [session:97344fc272] session_skills-hub.md\n"
            "# Segment Metadata — Session Skills Hub\n"
            "Administrative segment metadata.\n"
            "Not an executable skill.\n"
        ),
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)

    assert plan.outcome_kind == "unsupported"
    assert plan.exit_code == 3
    assert not plan.cards


def test_later_renderable_hit_wins_batch_even_if_first_hit_is_not_renderable() -> None:
    mod = load_module()
    payload = search_payload(
        {"ref": "repo:mystery-card.md:deadbeef", "score": 1.5},
        {"ref": "repo:tdd-coach.md:98be042492", "score": 1.1},
    )
    chunks = {
        "repo:mystery-card.md:deadbeef": (
            "## [repo:mystery-card.md:deadbeef] mystery-card.md\n"
            "Repository prose only, without trusted card fields.\n"
        ),
        "repo:tdd-coach.md:98be042492": (
            "## [repo:tdd-coach.md:98be042492] tdd-coach.md\n"
            "read /Users/felipe_gonzalez/.pi/agent/skills/tdd-coach/SKILL.md\n"
            "# Skill: tdd-coach\n"
            "**Source**: pi-agent-skills\n"
            "Use for TDD process coaching: RED-GREEN-REFACTOR cycle.\n"
        ),
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)

    assert plan.outcome_kind == "renderable_skill"
    assert plan.exit_code == 0
    assert [card.id for card in plan.cards] == ["tdd-coach"]


def test_stdin_search_output_malformed_json_exits_with_parse_error() -> None:
    result = subprocess.run(
        [sys.executable, str(HELPER_PATH), "--stdin-search-output", "--style", "plain"],
        input='{"hits": [}',
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "parse error" in result.stderr.lower()
    assert "empty" not in result.stderr.lower()


def test_stdin_search_output_invalid_structure_exits_with_parse_error() -> None:
    result = subprocess.run(
        [sys.executable, str(HELPER_PATH), "--stdin-search-output", "--style", "plain"],
        input='{"hits": "oops"}',
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "invalid hits list" in result.stderr.lower()
    assert "empty" not in result.stderr.lower()


def test_plain_and_rich_keep_same_batch_semantics_for_metadata_only() -> None:
    mod = load_module()
    payload = search_payload({"ref": "prime:efbc132df7", "score": 1.5})
    chunks = {
        "prime:efbc132df7": (
            "## [prime:efbc132df7] prime_skills-hub.md\n"
            "# Segment Metadata — Prime Skills Hub\n"
            "Administrative segment metadata.\n"
            "Not an executable skill.\n"
        )
    }

    plan = mod.build_render_plan(payload, chunks, limit=5)
    plain = mod.render_plain(plan)
    rich = strip_ansi(mod.render_rich(plan))

    assert plan.outcome_kind == "metadata_only"
    assert plan.exit_code == 3
    assert "administrative metadata" in plain.lower()
    assert "administrative metadata" in rich.lower()
