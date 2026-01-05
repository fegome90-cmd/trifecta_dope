#### 3.1.1 Definition of Done (DoD)

- [ ] Módulo `src/infrastructure/bundle_recorder.py` creado con:
  - `BundleRecorder.start_session(run_id, command, args)`
  - `BundleRecorder.log_tool_call(name, args, result, timing_ms)`
  - `BundleRecorder.log_file_read(path, lines_read, char_count)`
  - `BundleRecorder.log_pcc_metrics(metrics: dict)` **(NEW v1.1)** - integrar con `evaluate_pcc()`
  - `BundleRecorder.log_fp_gate_result(result: Result[ValidationResult, Err])` **(NEW v1.1)**
  - `BundleRecorder.finalize() -> Path` (genera manifest.json)
- [ ] Schema `bundle_manifest_v1.json` definido con campos mínimos:
