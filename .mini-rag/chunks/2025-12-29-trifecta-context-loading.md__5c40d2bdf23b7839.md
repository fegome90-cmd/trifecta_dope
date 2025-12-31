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
└───────────────────────────────────────────────────────────
