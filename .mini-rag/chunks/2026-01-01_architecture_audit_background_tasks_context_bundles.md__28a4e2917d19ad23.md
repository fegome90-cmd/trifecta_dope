```yaml
  schema_version: 1
  allow:
    - "*.md"
    - "_ctx/context_pack.json"
    - "_ctx/session_*.md"
  deny:
    - "node_modules/**"
    - ".git/**"
    - "**/*.pyc"
    - ".env"
    - "**/*secret*"
  limits:
    max_bundle_size_mb: 10
    max_file_reads: 100
    max_tool_calls: 50
  redaction:
    patterns:
      - 'api[_-]?key["\s:=]+[\w-]{20,}'
      - 'password["\s:=]+[^\s"]+'
  ```
- [ ] CLI wrapper en `cli.py`: Inicializar `BundleRecorder` al inicio de cada comando si `--bundle-capture` flag está presente.
- [ ] Test: `tests/unit/test_bundle_recorder.py` con 10 tests (start, log_tool_call, finalize, policy violations).
- [ ] Comando CLI: `trifecta bundle show <run_id>` para inspeccionar manifest (read-only).
