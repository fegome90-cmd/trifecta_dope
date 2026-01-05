#### 3.2.1 Definition of Done (DoD)

- [ ] Módulo `src/infrastructure/background_task_manager.py` con:
  - `BackgroundTaskManager.start(command, args) -> task_id`
  - `BackgroundTaskManager.status(task_id) -> TaskState`
  - `BackgroundTaskManager.tail(task_id, lines=20) -> str`
  - `BackgroundTaskManager.cancel(task_id) -> bool`
- [ ] State machine para tasks:
  ```
  PENDING → RUNNING → DONE
               ↓
             FAILED ← TIMEOUT
               ↓
           CANCELLED
  ```
- [ ] State file `_ctx/tasks/<task_id>/state.json`:
  ```json
  {
    "task_id": "task_abc123",
    "command": "trifecta ctx build",
    "args": {"segment": "."},
    "state": "RUNNING",
    "started_at": "2026-01-01T12:05:00Z",
    "updated_at": "2026-01-01T12:05:10Z",
    "pid": 12345,
    "log_path": "_ctx/tasks/task_abc123/output.log"
  }
  ```
- [ ] Lockfile `_ctx/tasks/<task_id>/task.lock` (fcntl) para evitar multi-writer.
- [ ] Report streaming: Task escribe a `output.log` (append-only), `tail` command lee últimas N líneas.
- [ ] Timeout policy: Si task > 10 mins sin heartbeat, marcar como TIMEOUT.
- [ ] CLI commands:
