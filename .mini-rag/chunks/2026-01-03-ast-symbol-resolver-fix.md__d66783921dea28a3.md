# AST/LSP Symbol Resolver Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the AST/LSP Symbol Resolver to correctly resolve Python module paths using dot-to-slash conversion.

**Architecture:** Minimal fix to SymbolResolver.resolve() in symbol_selector.py (L94-95) to convert Python module paths (with dots) to filesystem paths (with slashes). TDD approach with failing test first.

**Tech Stack:** Python, pytest, uv

---
