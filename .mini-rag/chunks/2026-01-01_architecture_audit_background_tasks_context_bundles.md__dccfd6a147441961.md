#### 3.2.4 Rollback Plan

- Si background tasks causan zombies: Implementar `cleanup` command que mata PIDs stale.
- Si lockfile corrupto: Eliminar `_ctx/tasks/<task_id>/*.lock` manualmente y re-start.
- Si state.json inválido: Comando `ps` marca como UNKNOWN y sugiere cleanup.

---
