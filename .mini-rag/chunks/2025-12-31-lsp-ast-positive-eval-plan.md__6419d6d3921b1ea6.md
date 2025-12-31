# LSP/AST Positive Eval Pack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a positive retrieval test set focused on LSP/AST topics with explicit expected hits and runnable bench integration.

**Architecture:** Add a dedicated query file and spec in `minirag-eval/`, update summary logic to include the new module, and wire the module into the combined query list.

**Tech Stack:** Bash scripts, Python (standard library), Mini-RAG CLI.

---
