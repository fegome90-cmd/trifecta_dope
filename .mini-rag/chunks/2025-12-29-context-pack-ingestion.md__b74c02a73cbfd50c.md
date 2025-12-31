### Isolation by Project

Each Trifecta segment has its own isolated context:

```
/projects/
├── debug_terminal/
│   ├── _ctx/
│   │   ├── context_pack.json    # Only for debug_terminal
│   │   └── context.db           # SQLite: only debug_terminal chunks (Phase 2)
│   └── skill.md
├── eval/
│   ├── _ctx/
│   │   ├── context_pack.json    # Only for eval
│   │   └── context.db           # SQLite: only eval chunks
│   └── skill.md
```

**No cross-contamination** between projects.

---
