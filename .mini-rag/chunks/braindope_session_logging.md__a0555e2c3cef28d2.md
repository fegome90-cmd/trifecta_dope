### Stack/Decisiones Técnicas Propuestas
- Script background (.sh) driven por agente
- Nuevo archivo: `_ctx/session_journal.jsonl`
- Metadata: timestamp, task_type, summary, files_touched, commands_executed, outcome, tags
- CLI query: `trifecta session query --type X --last N`
- session.md sigue existiendo (append-only, actualizado por tarea)
- JSONL es queryable vía `ctx`-like interface (context-as-tool)
