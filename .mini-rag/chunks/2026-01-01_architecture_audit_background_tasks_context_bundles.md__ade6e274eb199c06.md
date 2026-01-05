```bash
  trifecta background start "ctx build --segment ."  # Returns task_id
  trifecta background ps                              # List all tasks
  trifecta background tail <task_id>                  # Stream last 20 lines
  trifecta background cancel <task_id>                # Send SIGTERM
  ```
- [ ] Test: `tests/unit/test_background_task_manager.py` con 12 tests (state transitions, timeout, cancel, concurrent tasks).
- [ ] Integration test: `tests/test_background_integration.py` con real subprocess spawn.
