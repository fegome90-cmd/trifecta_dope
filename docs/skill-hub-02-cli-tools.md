# CLI Tools: Skill-Hub Ecosystem

This document details the command-line interfaces that power the skill-hub ecosystem.

### 1. skill-hub
- **Path:** `/Users/felipe_gonzalez/.local/bin/skill-hub`
- **Type:** bash
- **Size:** 4073 bytes, 153 lines
- **Purpose:** Primary CLI entry point for searching global skills with lightweight alias-aware reranking.
- **Dependencies:** `trifecta`, `skill-hub-cards`, `python3`
- **Called by:** Manual user invocation, agentic workflows

```bash
# Query parsing and Reranking logic
while [ $# -gt 0 ]; do
    case "$1" in
        --cards|-c) USE_CARDS=1; shift ;;
        --limit|-l) LIMIT="$2"; shift 2 ;;
        *) QUERY="$QUERY $1"; shift ;;
    esac
done
QUERY="${QUERY# }"

# Alias Matching via Python one-liner
if [ "$SHOULD_RERANK" -eq 1 ] && EXPLAIN_JSON="$(... --explain --explain-format json 2>/dev/null)"; then
    CANONICAL_ALIAS_MATCH="$(EXPLAIN_JSON="$EXPLAIN_JSON" python3 - <<'PY'
import json, os, re
data = json.loads(os.environ.get("EXPLAIN_JSON", ""))
expanded_terms = data.get("expansions", {}).get("expanded_terms", [])
hits = data.get("hits", [])
# Logic to detect if a term matches a hit that isn't the top one
...
PY
)"
fi

# Search Execution
if [ "$USE_CARDS" -eq 1 ]; then
    python3 "$CARDS_HELPER" "$QUERY" --limit "$LIMIT"
else
    MAIN_OUTPUT="$(run_search_capture --query "$QUERY")"
    printf '%s\n' "$MAIN_OUTPUT"
fi
```

---

### 2. skill-hub-cards
- **Path:** `/Users/felipe_gonzalez/.local/bin/skill-hub-cards`
- **Type:** python
- **Size:** 326 bytes, 15 lines
- **Purpose:** Thin wrapper/entry point for the Python-based card rendering engine.
- **Dependencies:** `skill_hub_cards_core.py`
- **Called by:** `skill-hub` when `--cards` flag is used.

```python
#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from skill_hub_cards_core import cli  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(cli())
```

---

### 3. skill_hub_cards_core.py
- **Path:** `/Users/felipe_gonzalez/.local/bin/skill_hub_cards_core.py`
- **Type:** python
- **Size:** 19128 bytes, 606 lines
- **Purpose:** Core engine for skill discovery, result normalization, and multi-style rendering (Plain Markdown vs. Rich Terminal UI).
- **Dependencies:** `trifecta` (via subprocess), `rich` (optional)
- **Called by:** `skill-hub-cards`
- **Key Features:**
    - **Normalization:** Converts raw Trifecta hits into `SkillCard` objects by extracting paths, sources, and useful descriptions using regex patterns.
    - **Classification:** Filters out "administrative metadata" (e.g., segment metadata) to ensure only actionable skills are rendered.
    - **Rendering Styles:**
        - `plain`: Agent-friendly Markdown format (`# Skill: ...`, `read ...`).
        - `rich`: Human-friendly TUI using `rich.panel` with specific color tokens (e.g., `grey37` borders, `grey19` background for the "READ" CTA).

```python
# Key Data Structures
@dataclass(frozen=True)
class NormalizedResult:
    ref: str
    visible_title: str | None
    path: str | None
    description: str | None
    # ...

# Search + Render Pipeline
def cli(argv: list[str] | None = None) -> int:
    raw_search_output = _load_search_payload(args)
    hits = parse_search_output(raw_search_output)
    chunk_texts = run_get(hit.ref for hit in hits) # Get content
    plan = build_render_plan(raw_search_output, chunk_texts)
    
    # Rendering decision
    rendered = output_json(plan) if args.json else (
        render_rich(plan) if args.style == "rich" else render_plain(plan)
    )
```

---

### 4. skill-hub-health
- **Path:** `/Users/felipe_gonzalez/.local/bin/skill-hub-health`
- **Type:** bash
- **Size:** 3386 bytes, 114 lines
- **Purpose:** Smoke test utility to ensure CLI responsiveness and correctness.
- **Dependencies:** `skill-hub`, `timeout`, `grep`
- **Called by:** Developers, CI/CD pipelines

```bash
# Test Cases and Timeout Handling
run_tests() {
    # Test 1: Single word (Direct match)
    check "single word, plain" 'skill-hub "security" --plain --limit 3'

    # Test 2: Multi-word (Reranking/Expansion)
    check "multi word, plain" 'skill-hub "how to debug async code" --plain --limit 3'

    # Test 6: Security/Sanity Check
    # Ensures no active heredoc patterns (<<<) are present in the bash script
    # to avoid shell-injection-like risks in query handling.
    heredoc_lines=$(grep -n '<<<' ~/.local/bin/skill-hub | grep -cv 'NOTE:\|#' || true)
}
```
