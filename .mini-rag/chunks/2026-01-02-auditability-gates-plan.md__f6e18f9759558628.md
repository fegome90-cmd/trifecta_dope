# Trifecta Quality Plan — Auditability Gates (Fail-Closed) - FINAL

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **CORRECCIONES APLICADAS:**
> - G2: Exit codes preservados (sin pipes que rompan RC)
> - G2: Integration tripwire agregado (ctx sync + validación JSON completo)
> - G1: Opción B elegida (arreglar imports en tests, NO re-exports)
> - G3: Sin flags nuevos (resolución desde segment_root + src/)
> - audit_repro.sh: Política unificada con RC explícitos

**Goal:** Transform trifecta_dope from "non-auditable" to "auditable-by-default" con gates fail-closed.

**Architecture:** Patches mínimos; sin nuevos sistemas; AST-primary; LSP enhancement.

**Tech Stack:** Python 3.12+, pytest, uv, tree-sitter (optional), JSONL telemetry.

---
