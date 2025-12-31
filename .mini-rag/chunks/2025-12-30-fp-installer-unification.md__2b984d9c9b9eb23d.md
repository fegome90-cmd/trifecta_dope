# FP Installer Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `scripts/install_FP.py` the canonical installer by adding missing validations and legacy-name warnings while keeping dynamic naming and no auto-renames.

**Architecture:** Add a pure validation helper in `src/infrastructure/validators.py` to detect legacy context filenames, and wire it into the FP installer. Keep installation side effects in the script and keep validators pure.

**Tech Stack:** Python 3.12, Typer CLI (indirect), pytest, uv
