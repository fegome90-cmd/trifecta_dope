## OVERVIEW

This plan splits telemetry instrumentation into **2 clean phases**:

**PR#1 (Telemetry Extension):** Extend `src/infrastructure/telemetry.py` to support AST/LSP event types, reserved key protection, path normalization, and new aggregation summaries. **No AST/LSP implementation** — only scaffolding, types, and tests.

**PR#2 (AST/LSP Implementation):** Implement Tree-sitter parser, Pyright LSP client, symbol selector, and progressive disclosure logic. Consumes telemetry hooks from PR#1.
