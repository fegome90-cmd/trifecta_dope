### [P1] 5. LSP Client Shutdown Race Condition

- **Señal (command)**: `rg 'join\(|terminate\(|BrokenPipeError' src`
- **Ubicación**: `src/infrastructure/lsp_client.py:142-154`
- **Riesgo**: Shutdown sequence does `terminate()` -> `wait()` -> `thread.join()` -> close streams. If thread is still reading when streams close, `BrokenPipeError` or `ValueError: I/O operation on closed file` can occur.
- **Fix lean** (<= 60 líneas):
  ```python
  # Current: terminate -> wait -> join -> close
  # Fixed:
  self._stopping.set()  # Signal stop first
  self._thread.join(timeout=1.0)  # Let thread exit cleanly
  if self._thread.is_alive():  # Thread still alive, force kill
      self.process.terminate()
      self.process.wait(timeout=0.5)
  # Only close streams AFTER thread is dead
  self.stdin.close()
  self.stdout.close()
  ```
- **Tripwire test**: `test_shutdown_no_broken_pipe`
  ```python
  def test_shutdown_no_broken_pipe(capfd):
      client = LSPClient(...)
      client.shutdown()
      captured = capfd.readouterr()
      assert "BrokenPipeError" not in captured.err
      assert "I/O operation on closed file" not in captured.err
  ```
- **Evidencia requerida**: `pytest tests/integration/test_lsp_no_stderr_errors.py -v`

---
