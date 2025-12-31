# Claude Code CLI Hooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a reliable pre/post hook flow for Claude Code CLI that always updates `session_ast.md`, gates on `trifecta ctx sync/validate`, and fail-closes on errors.

**Architecture:** Implement a wrapper launcher that intercepts Claude CLI runs, writes a structured Run Record into `_ctx/session_<segment>.md` with locking, and enforces sync/validate. Add a CI gate to ensure session updates accompany code/doc changes.

**Tech Stack:** Python (wrapper + session writer), shell launcher, existing Trifecta CLI, pytest.
