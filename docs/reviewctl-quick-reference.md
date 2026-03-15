# Reviewctl Quick Reference

## Preparation

```bash
export REVIEW_API_TOKEN=...
mkdir -p apps/pae-wizard/outputs/reviewctl
```

## Static commands

```bash
bun run lint:biome
bun run lint:ruff
```

## Branch review flow

```bash
bun /Users/felipe_gonzalez/Developer/branch-review/mini-services/reviewctl/src/index.ts init --create
bun /Users/felipe_gonzalez/Developer/branch-review/mini-services/reviewctl/src/index.ts explore context
bun /Users/felipe_gonzalez/Developer/branch-review/mini-services/reviewctl/src/index.ts explore diff
bun /Users/felipe_gonzalez/Developer/branch-review/mini-services/reviewctl/src/index.ts plan
bun /Users/felipe_gonzalez/Developer/branch-review/mini-services/reviewctl/src/index.ts run
```
