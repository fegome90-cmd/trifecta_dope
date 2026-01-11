# Trifecta Quality Plan — Auditability Gates (Fail-Closed) v2.0

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **ANTI-PATRONES EXPLÍCITOS:** Este plan evita AP1-AP10. Cada sección lista los anti-patrones evitados.
>
> **FILOSOFÍA:** Fail-closed + simplicidad operable + determinismo + auditabilidad por defecto.
> Cambios mínimos con ROI alto. Nada de refactors grandes.

**Goal:** Transformar trifecta_dope de "no-auditable" a "auditable-by-default" con gates fail-closed.

**Architecture:** Patches mínimos; sin nuevos sistemas; AST-primary; LSP enhancement.

**Tech Stack:** Python 3.12+, pytest, uv, tree-sitter (optional), JSONL telemetry.

---
