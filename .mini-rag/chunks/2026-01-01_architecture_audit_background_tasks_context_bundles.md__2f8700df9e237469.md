#### 3.1.2 Tests Required

| Test | Assertion | Coverage |
|------|-----------|----------|
| `test_bundle_recorder_start_session` | `manifest.json` creado con run_id correcto | Happy path |
| `test_log_tool_call_with_redaction` | API key en result es redactado (`***`) | Redaction policy |
| `test_finalize_generates_sha256` | SHA256 digest matches computed hash | Integrity |
| `test_policy_deny_node_modules` | File read de `node_modules/x.js` es bloqueado | Denylist enforcement |
| `test_max_tool_calls_limit` | Error si > 50 tool calls registrados | Bloat protection |
| `test_bundle_capture_disabled_by_default` | Sin flag `--bundle-capture`, recorder es noop | Backward compat |
| `test_concurrent_recorders_isolated` | Dos run_ids diferentes no se cruzan | Isolation |
| `test_file_read_outside_segment_blocked` | Read de `/etc/passwd` es prohibido | Security scope |
| `test_bundle_finalization_retry` | Retry 3 veces si write fail, luego warning | Resilience |
| `test_bundle_show_command_output` | CLI muestra manifest en formato legible | UX |
| `test_log_pcc_metrics_integration` **(NEW v1.1)** | PCC metrics grabados en manifest con estructura correcta | PCC integration |
| `test_log_fp_gate_result_ok_and_err` **(NEW v1.1)** | FP Gate Ok/Err se serializa correctamente en manifest | Result monad integration |
