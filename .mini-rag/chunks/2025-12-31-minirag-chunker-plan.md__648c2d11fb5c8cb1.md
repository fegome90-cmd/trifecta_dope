# Mini-RAG Chunker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a local Markdown-aware chunker that generates coherent chunks into `.mini-rag/chunks/` and wires it into the Mini‑RAG indexing flow.

**Architecture:** Pure parsing/chunking functions in `scripts/minirag_chunker.py`, with a small CLI wrapper to read config and emit chunk files + a manifest. Mini‑RAG’s indexer continues to read plain `.md` files via `docs_glob` pointing at the generated chunks.

**Tech Stack:** Python 3.12, pytest, PyYAML, standard library (`hashlib`, `argparse`, `pathlib`).

---
