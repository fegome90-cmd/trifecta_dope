### [P0] 2. LSP Daemon `time.sleep` Flakes in Integration Tests

- **Señal (command)**: `rg 'time\.sleep' tests`
- **Ubicación**: `tests/integration/test_lsp_daemon.py:52,89,146,150,178,221,242,262,324,328,362`
- **Riesgo**: 11 `time.sleep()` calls (up to 3.5s) make daemon tests flaky on slow CI runners. False green when sleep is too short, false red on slow machines.
- **Fix lean** (<= 60 líneas):
  ```python
  # Replace time.sleep with Event-based wait
  def wait_for_condition(predicate, timeout=5.0, poll=0.05):
      deadline = time.monotonic() + timeout
      while time.monotonic() < deadline:
          if predicate():
              return True
          time.sleep(poll)
      return False
  ```
  Apply to daemon ready, lock acquisition, TTL expiry checks.
- **Tripwire test**: `test_daemon_ready_uses_event_not_sleep`
  ```python
  def test_daemon_ready_uses_event_not_sleep(monkeypatch):
      sleep_calls = []
      monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))
      # ... start daemon, wait for ready ...
      assert all(s <= 0.1 for s in sleep_calls), "No long sleeps allowed"
  ```
- **Evidencia requerida**: `pytest tests/integration/test_lsp_daemon.py -v --tb=short`

---
