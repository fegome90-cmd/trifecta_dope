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
