# PR Plan: Telemetry Extension for AST+LSP (2-Phase, Corrected)

**Date:** 2026-01-01  
**Version:** 2.2 (PASS - Ready for Implementation)  
**Role:** Senior Engineer / Patch Agent  
**Scope:** 2 PRs over 5–6 days (PR#1: 2 days, PR#2: 3-4 days)  
**Success Criterion:** Zero corruption (valid JSON lines), <2% drop rate (tracked via telemetry_lock_skipped), monotonic timings, zero duplicate systems, >80% test coverage. Loss acceptable for analytics ONLY, never for gates.

---
