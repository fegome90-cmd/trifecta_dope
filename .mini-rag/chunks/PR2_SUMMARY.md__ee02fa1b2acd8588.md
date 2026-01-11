### LSP READY Detection
- **Issue:** publishDiagnostics may be delayed
- **Mitigation:** Warm-up happens in parallel (non-blocking)
- **Future:** Add timeout for warm-up phase (e.g., 5s max)
