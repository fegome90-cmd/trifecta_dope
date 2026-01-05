### A.4 Background Task → State Machine Updates

**Archivo**: `src/infrastructure/background_task_manager.py` (nuevo)

**Estado tracking**: Cada transición escribe a `_ctx/tasks/<task_id>/state.json` con lock.

```python
# background_task_manager.py (nuevo archivo)

class BackgroundTaskManager:
    def _update_state(self, task_id: str, new_state: str):
        state_path = self._task_dir(task_id) / "state.json"
        lock_path = self._task_dir(task_id) / "task.lock"

        with file_lock(lock_path):
            state = json.loads(state_path.read_text())
            state["state"] = new_state
            state["updated_at"] = datetime.now().isoformat()
            state["state_history"].append({"state": new_state, "timestamp": state["updated_at"]})

            AtomicWriter.write(state_path, json.dumps(state, indent=2))
```

---
