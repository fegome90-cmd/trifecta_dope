# Reviewctl Agent Guide

Use `reviewctl` from the repository root.

## Repo-specific static commands

- `bun run lint:biome`
- `bun run lint:ruff`

## Expected diff scope

- Base branch is `main`
- The review branch is the current checked out branch
- Static checks are diff-scoped using `main...HEAD`

## Notes for this repo

- `biome` is present only to provide parser-conclusive output for `reviewctl`
- `ruff` uses the existing Ruff configuration from `pyproject.toml`
- The frontend gate is disabled in `.reviewctl/project-gates.json`
