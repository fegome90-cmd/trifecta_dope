# Audit 2: Real-World Bug Hunter Report

**Change**: skill-hub-render-unification
**Skill**: real-world-bug-hunter
**Date**: 2026-05-01
**Agents**: Ripper (38 cmds), Walker (12 tests), Sniper (9 tests)
**Status**: COMPLETE

## Methodology

Three specialized sub-agents ran real commands against the CLI and bash wrapper:
- **Ripper**: Rapid boundary probing — 38 commands covering injection, encoding, flags, limits
- **Walker**: Targeted behavioral verification — 12 tests on known/suspected issues
- **Sniper**: Cross-boundary isolation — concurrency, temp files, env manipulation, kill recovery

## Cross-Confirmed Findings

| Finding | Ripper | Walker | Sniper | MR-Audit |
|---------|--------|--------|--------|----------|
| Exit code 0 for rejected queries | partial | HIGH | HIGH | 4/4 agents |

## HIGH (5 unique)

### H-1: Exit code 0 for rejected queries
- **Location**: `cards_core.py:538`
- **Description**: `cli()` returns EXIT_RENDERABLE (0) for empty/whitespace queries instead of EXIT_ERROR (1) or EXIT_EMPTY (4)
- **Impact**: Downstream consumers checking exit codes think query succeeded
- **Confirmed by**: 4 independent sources (Walker, Sniper, MR-Thorough 4/4 agents, Ripper partial)
- **Fix**: Change `return EXIT_RENDERABLE` to `return EXIT_EMPTY` at line 538

### H-2: Bash wrapper swallows --style and --json flags
- **Location**: `scripts/skill-hub` (bash wrapper)
- **Description**: `--style rich` and `--json` interpreted as query text, not flags
- **Impact**: Users cannot use rich rendering or JSON output via bash wrapper
- **Fix**: Add --style and --json passthrough in wrapper's arg parser

### H-3: Null byte silently truncates query
- **Location**: `sanitize_query()` in cards_core.py
- **Description**: `$'test\x00null'` searches only "test" — null bytes stripped silently
- **Impact**: Silent data loss, user unaware query was modified
- **Fix**: Return warning or reject queries containing null bytes

### H-4: --cards bypasses whitespace validation
- **Location**: cards_core.py vs plain mode
- **Description**: Plain mode rejects `'   '` with clear message; --cards accepts it
- **Impact**: Inconsistent validation between modes
- **Fix**: Apply same whitespace validation in cards mode

### H-5: No --limit upper bound
- **Location**: argparse + cards_core.py
- **Description**: `--limit 999999` dumps 62+ results / 550+ lines
- **Impact**: DoS vector in automation contexts
- **Fix**: Cap --limit at reasonable maximum (e.g. 50)

## MEDIUM (8 unique)

| ID | Finding | Location |
|----|---------|----------|
| M-1 | Fake refs produce DEGRADED cards indistinguishable from real data | --stdin-search-output |
| M-2 | Bash wrapper exit code inconsistent with CLI | scripts/skill-hub |
| M-3 | Misleading tip in stdin mode (query_hint=None) | header rendering |
| M-4 | 8192-char query not rejected, full length echoed | sanitize_query |
| M-5 | RTL override (U+202E) preserved in output | terminal rendering |
| M-6 | BOM character silently changes search semantics | sanitize_query |
| M-7 | --cards '' shows plain-text usage instead of card-format error | cli() |
| M-8 | HOME override causes unrecoverable crash (uv cache) | environment |

## LOW (6 unique)

| ID | Finding |
|----|---------|
| L-1 | SQL injection string rendered verbatim in header (cosmetic) |
| L-2 | RTL override in cards Query echo (visual spoofing) |
| L-3 | Empty PATH causes Python traceback (no user-friendly error) |
| L-4 | Dash-only query returns exit 0 (ambiguous) |
| L-5 | Boundary cases all pass correctly: limit 0, limit 100, injection safe, truncation |

## Isolation PASSES

- ✅ Concurrent invocations: no data leakage, no temp file collision
- ✅ Temp file cleanup: EXIT trap working correctly
- ✅ Kill during execution: clean cleanup, no leftover files
- ✅ Error recovery: invalid segment → normal call recovers cleanly
- ✅ No injection vulnerabilities: SQL, shell, template, XSS, path traversal all safe

## Summary

| Metric | Count |
|--------|-------|
| Total unique findings | 19 |
| CRITICAL | 0 |
| HIGH | 5 |
| MEDIUM | 8 |
| LOW | 6 |
| Cross-confirmed | 1 |

## Top Priority Fix

**H-1** — Single-line fix at `cards_core.py:538`: change `return EXIT_RENDERABLE` to `return EXIT_EMPTY` for rejected queries. Most impactful, confirmed by 4 independent sources.
