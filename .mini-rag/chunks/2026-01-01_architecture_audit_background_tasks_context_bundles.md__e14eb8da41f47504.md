#### 3.2.2 Tests Required

| Test | Assertion | Coverage |
|------|-----------|----------|
| `test_start_task_creates_state_file` | `state.json` existe con state=PENDING | Happy path |
| `test_task_transitions_to_running` | Después de spawn, state=RUNNING | State machine |
| `test_task_transitions_to_done_on_success` | Exit 0 → state=DONE | Success path |
| `test_task_transitions_to_failed_on_error` | Exit 1 → state=FAILED | Error path |
| `test_timeout_marks_task_as_timeout` | Mock 10min delay → state=TIMEOUT | Timeout policy |
| `test_cancel_sends_sigterm` | cancel() envía SIGTERM a PID | Cancellation |
| `test_concurrent_tasks_isolated` | Task A y Task B no comparten state | Isolation |
| `test_lockfile_prevents_multi_writer` | Segundo start con mismo task_id falla con error | Concurrency safety |
| `test_tail_reads_last_20_lines` | tail() retorna últimas 20 líneas de output.log | Streaming |
| `test_ps_lists_all_tasks` | ps() retorna lista de task_ids con states | Discovery |
| `test_stale_lock_cleanup` | Lock > 1hr sin heartbeat es removido | Stale lock detection |
| `test_task_output_log_rotation` | Log > 5MB → rotate (keep last 2 files) | Bloat protection |
