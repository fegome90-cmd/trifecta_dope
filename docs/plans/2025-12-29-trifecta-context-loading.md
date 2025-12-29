# Trifecta Context Loading — Simplified Plan

**Date**: 2025-12-29  
**Status**: Design Revised  
**Approach**: Heuristic file loading (no RAG, no chunking)
**Name**: Programming Context Caller (PCC) - Simplified
---

## Problem Statement

**Original approach was over-engineered:**
- ❌ RAG/chunking for 5 small files (unnecessary)
- ❌ LLM-based orchestrator (overkill)
- ❌ HemDov-specific (not agent-agnostic)
- ❌ Ignoring existing Trifecta system

**Correct approach:**
- ✅ Load complete files (not chunks)
- ✅ Heuristic selection (keyword matching)
- ✅ Agent-agnostic (works with any LLM)
- ✅ Use existing Trifecta CLI

---

## Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│  User Task: "Implement DT2-S1 in debug_terminal"            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Trifecta CLI (heuristic file selector)                     │
├─────────────────────────────────────────────────────────────┤
│  1. Parse task → extract keywords                           │
│  2. Match keywords to file types                            │
│  3. Load complete files (no chunking)                       │
│  4. Format as markdown                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Agent Context (enriched)                                   │
├─────────────────────────────────────────────────────────────┤
│  System Prompt:                                             │
│  - Task: "Implement DT2-S1..."                              │
│  - Context Files:                                           │
│    * skill.md (Core Rules)                                  │
│    * agent.md (Stack & Architecture)                        │
│  Total: ~3-5 KB (manageable for any LLM)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Heuristic Selection Rules

```python
def select_files(task: str, segment: str) -> list[str]:
    """
    Select relevant Trifecta files based on task keywords.
    No LLM needed - simple heuristics.
    """
    files = []
    task_lower = task.lower()
    
    # ALWAYS include skill.md (core rules)
    files.append(f"{segment}/skill.md")
    
    # Implementation/debugging → agent.md
    if any(kw in task_lower for kw in ["implement", "debug", "fix", "build"]):
        files.append(f"{segment}/agent.md")
    
    # Planning/design → prime.md
    if any(kw in task_lower for kw in ["plan", "design", "architecture"]):
        files.append(f"{segment}/prime.md")
    
    # Session review/handoff → session.md
    if any(kw in task_lower for kw in ["session", "handoff", "history", "previous"]):
        files.append(f"{segment}/session.md")
    
    # Always include README for quick reference
    files.append(f"{segment}/README_TF.md")
    
    return files
```

**No chunking. No RAG. No LLM orchestrator.**

---

## CLI Interface (Using Existing Trifecta)

```bash
# Load context for a task
trifecta load --segment debug_terminal --task "implement DT2-S1"

# Output: Markdown with skill.md + agent.md content
# Agent receives complete files, not chunks
```

**Integration with any agent:**
```python
# Works with Claude, Gemini, GPT, etc.
from trifecta import load_context

context = load_context(
    segment="debug_terminal",
    task="implement DT2-S1 sanitization"
)

# context = markdown string with complete files
# Inject into system prompt
agent.run(system_prompt=f"Task: ...\n\nContext:\n{context}")
```

---

## Why This is Better

| Aspect | Complex (PCC/RAG) | Simple (Heuristic) |
|--------|-------------------|-------------------|
| **Complexity** | High (chunking, scoring, LLM) | Low (keyword matching) |
| **Token usage** | ~2000 (chunks) | ~3000 (complete files) |
| **Accuracy** | May miss context | Complete coverage |
| **Latency** | High (LLM orchestrator) | Low (instant) |
| **Maintenance** | Complex (scoring tuning) | Simple (keyword rules) |
| **Agent support** | HemDov-specific | Any agent |

**For 5 small files, simple is better.**

---

## Implementation (Using Existing Trifecta)

### 1. Extend Trifecta CLI

**File**: `trifecta_dope/src/infrastructure/cli.py`

Add `load` command:
```python
@app.command()
def load(
    segment: str,
    task: str,
    output: Optional[str] = None
):
    """Load context files for a task."""
    files = select_files(task, segment)
    context = format_context(files)
    
    if output:
        Path(output).write_text(context)
    else:
        print(context)
```

### 2. File Selector

**File**: `trifecta_dope/src/application/context_loader.py` (NEW)

```python
from pathlib import Path

def select_files(task: str, segment: str) -> list[Path]:
    """Select files based on task keywords."""
    base = Path(f"/projects/{segment}")
    files = []
    task_lower = task.lower()
    
    # Always skill.md
    files.append(base / "skill.md")
    
    # Conditional files
    if any(kw in task_lower for kw in ["implement", "debug", "fix"]):
        files.append(base / "_ctx/agent.md")
    
    if any(kw in task_lower for kw in ["plan", "design"]):
        files.append(base / "_ctx/prime.md")
    
    if any(kw in task_lower for kw in ["session", "handoff"]):
        files.append(base / "_ctx/session.md")
    
    files.append(base / "README_TF.md")
    
    return [f for f in files if f.exists()]

def format_context(files: list[Path]) -> str:
    """Format files as markdown."""
    sections = []
    
    for file in files:
        content = file.read_text()
        sections.append(f"## {file.name}\n\n{content}")
    
    return "\n\n---\n\n".join(sections)
```

---

## Phase 1: MVP (Today)

### Deliverables

1. **`context_loader.py`** - Heuristic file selector
2. **Extend Trifecta CLI** - Add `load` command
3. **Tests** - Test file selection for sample tasks

### Exit Criteria

- ✅ `trifecta load` works for any segment
- ✅ Correct files selected for test tasks
- ✅ Output is valid markdown
- ✅ Works with any agent (not just HemDov)

---

## Example Usage

**Task**: "Implement DT2-S1 sanitization in debug_terminal"

**Command**:
```bash
trifecta load --segment debug_terminal --task "implement DT2-S1"
```

**Output**:
```markdown
## skill.md

# Debug Terminal - Skill

## Core Rules
1. **Sync First**: Validate .env...
2. **Test Locally**: Run pytest...
...

---

## agent.md

# Debug Terminal - Agent Context

## Stack
- Python 3.12
- tmux for cockpit
...

---

## README_TF.md

# Debug Terminal - Trifecta Documentation
...
```

**Agent receives**: Complete files, no chunking, no RAG.

---

## Success Criteria

- [ ] Heuristic file selector implemented
- [ ] Trifecta CLI `load` command working
- [ ] Tests passing
- [ ] Works with any agent (Claude, Gemini, GPT)
- [ ] Simpler than original PCC plan

---

## References

- Trifecta CLI: `trifecta_dope/src/infrastructure/cli.py`
- Original (over-engineered) plan: Replaced by this simplified approach
