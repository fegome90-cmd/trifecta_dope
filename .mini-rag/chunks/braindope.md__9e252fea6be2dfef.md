# 7) Session Log (`session_<segment>.md`) — Perfil `handoff_log`

Archivo de runtime con perfil fijo:

```markdown
---
segment: eval-harness
profile: handoff_log
output_contract:
  append_only: true
  require_sections: [History, NextUserRequest]
  max_history_entries: 10
  entry_fields: [user_prompt_summary, agent_response_summary]
  forbid: [refactors, long_essays]
---

# Active Session
- **Objetivo**: 
- **Archivos a tocar**: 
- **Gates a correr**: 
- **Riesgos detectados**: 

---

# History
```yaml
- session:
    timestamp: "2025-12-28T09:30:00"
    user_prompt_summary: "Fix memory tool selection gap"
    agent_response_summary: "Updated semantic_router.py, accuracy 95.5%"
    files_touched: ["semantic_router.py"]
    outcome: "Success"
```

# Next User Request
<!-- El siguiente agente comienza aquí -->
```

---
