| Background task timeout (10min) funcional | ☐ | ☐ | Task sin heartbeat > 10min → state=TIMEOUT |
| **V12** | Bundle replay no ejecuta side-effects (dry-run only) | ☐ | ☐ | FileSystemAdapter.write() es mock en replay mode |
| **V13** | Session append usa AtomicWriter (no half-writes) | ☐ | ☐ | `SessionAppendUseCase` usa `AtomicWriter.write()` |
| **V14** | Fail-closed: Bundle pack abort si policy violation | ☐ | ☐ | `fail_policy: fail_loudly` fuerza abort |
| **V15** | Bundle manifest SHA256 es verificable | ☐ | ☐ | `sha256 manifest.json` matches `metadata.sha256_digest` |
| **V16 (NEW v1.1)** | PCC metrics capturados en bundle manifest | ☐ | ☐ | `pcc_metrics` field con path_correct/false_fallback/safe_fallback |
| **V17 (NEW v1.1)** | FP Gate result serializado en manifest | ☐ | ☐ | `fp_gate_result` con status ok/err y validation details |
