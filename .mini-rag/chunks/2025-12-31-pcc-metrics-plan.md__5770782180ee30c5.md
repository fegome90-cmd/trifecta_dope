# PCC Tool-Calling Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend `trifecta ctx eval-plan` to output PCC tool-calling metrics (path correctness, safe vs false fallback, guardrails) using PRIME feature_map, and document the spec in an ADR.

**Architecture:** Add a small PCC metrics helper to parse PRIME `index.feature_map`, then compute per-task PCC outcomes using existing eval-plan results (selected_feature, paths, selected_by). Keep dataset unchanged.

**Tech Stack:** Python 3.12+, Typer CLI, Pytest, Markdown ADR.

---
