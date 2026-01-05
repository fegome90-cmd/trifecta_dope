# T9.3.5 Scoring Fix Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix L2 scoring clamp + telemetry/debug reporting per T9.3.5 spec, then regenerate eval artifacts with consistent evidence.

**Architecture:** Keep core L2 matching deterministic. Add temporary instrumentation for diagnosis, then remove it. Make clamp behavior explicit when blocking top single-word triggers, and compute top_k after sorting.

**Tech Stack:** Python 3.12+, Typer CLI, Pytest, Mini-RAG CLI.

---
