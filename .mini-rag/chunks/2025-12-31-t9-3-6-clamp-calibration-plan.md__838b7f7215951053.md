# T9.3.6 Clamp Calibration + Stabilization (Router v1) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a clamp impact report, calibrate the single-word clamp via config-driven support terms, re-evaluate against the same dataset, and freeze Router v1 via ADR.

**Architecture:** Keep L2 matching deterministic with score/specificity/priority ordering and tie-to-fallback. Move support term checks into aliases.yaml for observability_telemetry only, and emit explicit telemetry fields for clamp decisions.

**Tech Stack:** Python 3.12+, Typer CLI, Pytest, uv, Markdown docs.

---
