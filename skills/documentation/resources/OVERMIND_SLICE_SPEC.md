# Overmind Slice Spec — Phase 1 (Revised)

## 1. Executive Summary

- **Ownership Signal**: Detects docs without owner via CODEOWNERS (lite parser) or frontmatter. Opt-in via OWNERSHIP_REQUIRED=1. Can emit WARN.
- **ADR Signal**: Detects Architecture Decision Records in docs/adr/ or docs/decisions/. Opt-in (activates if dir exists or ADR_REQUIRED=1). Can emit FAIL when ADR_REQUIRED=1.
- **Coverage-Lite Signal**: Heuristic ratio docs/src with configurable directories, excludes generated code AND empty docs (<100 chars).
- **Offline-first**: Pre-commit never calls network. External link checks emit SKIP offline, WARN only with --online.
- **Blocking Policy**: Single source of truth - FAIL blocks, WARN does NOT block (unless --strict). Health Score is FYI only.
- **WO PROHIBITED**: Hard guard - paths matching `_ctx/`, `WO-*.yaml`, `backlog.yaml` always SKIP.

---

## 2. Scope

### IN (Phase 1)
- Ownership signal (opt-in)
- ADR signal (opt-in)
- Coverage-lite signal (configurable)
- JSON schema with schema_version

### OUT
- Work Orders (WO) — PROHIBITED
- Backstage/TechDocs
- Vale linting
- GitHub Actions docs-lint (Phase 2 roadmap only)
- Auto-patching

---

## 3. Phase 1 Deliverables

| Signal | Config Key | Default | Trigger | Output |
|--------|------------|---------|---------|--------|
| **ownership** | OWNERSHIP_REQUIRED | 0 (off) | If OWNERSHIP_REQUIRED=1 | WARN if doc lacks owner |
| **adr** | ADR_REQUIRED | 0 (off) | If ADR_REQUIRED=1 OR docs/adr/ exists | WARN if stale >180d or missing index |
| **coverage** | COVERAGE_MODE | "lite" | Always | INFO if ratio <0.1, WARN if <0.05 |
| **external_links** | (automatic) | SKIP | --online flag | SKIP offline, WARN online |

---

## 4. Severity Policy

| Status | Meaning | Score Impact | Pre-commit Blocks? |
|--------|---------|--------------|-------------------|
| **INFO** | FYI, no action required | 0 | No |
| **WARN** | Should fix, not critical | -5 | No (unless --strict) |
| **FAIL** | Must fix before proceed | -15 | YES |
| **SKIP** | Not applicable / offline | 0 | No |

**SINGLE SOURCE OF TRUTH - Blocking Policy**:
```
block_if = (any FAIL) OR (--strict AND any WARN)
```
- Score is FYI only (informational)
- WARN never blocks unless --strict is used
- FAIL always blocks

**Invariants**:
- INFO/WARN: Never FAIL unless explicitly required (ADR_REQUIRED=1)
- External links: SKIP when offline, WARN with --online
- WO paths (_ctx/, _ctx/jobs/, WO-*.yaml): PROHIBITED - always SKIP

---

## 4B. Activation Matrix (SSOT)

This matrix defines all possible states per signal. Used as single source of truth for implementation and tests.

### Ownership Signal
| Config | Source | Status | Reason |
|--------|--------|--------|--------|
| OWNERSHIP_REQUIRED=0 | any | SKIP | Not activated |
| OWNERSHIP_REQUIRED=1 | CODEOWNERS parsed | PASS | All docs have owner |
| OWNERSHIP_REQUIRED=1 | CODEOWNERS parsed | WARN | Some docs unowned |
| OWNERSHIP_REQUIRED=1 | CODEOWNERS too complex | WARN | Parser failed, require frontmatter |
| OWNERSHIP_REQUIRED=1 | no source found | INFO | No ownership source |

### ADR Signal
| Config | Dir Exists | Index | Staleness | Status | Reason |
|--------|-------------|-------|-----------|--------|--------|
| ADR_REQUIRED=0 | No | - | - | SKIP | Not activated |
| ADR_REQUIRED=0 | Yes | any | any | INFO | Dir exists but not required |
| ADR_REQUIRED=1 | No | - | - | FAIL | Required but missing |
| ADR_REQUIRED=1 | Yes | No | any | WARN | No index |
| ADR_REQUIRED=1 | Yes | Yes | <=180d | PASS | Healthy |
| ADR_REQUIRED=1 | Yes | Yes | >180d | WARN | Stale |
| any | any | any | git fail | INFO | Cannot determine |

### Coverage-Lite Signal
| Mode | Ratio | Status | Reason |
|------|-------|--------|--------|
| COVERAGE_MODE=off | - | SKIP | Disabled |
| lite/full | src=0 | INFO | No source to compare |
| lite/full | <0.05 | WARN | Critical gap |
| lite/full | 0.05-0.1 | INFO | Low but acceptable |
| lite/full | >=0.1 | PASS | Healthy |

### External Links
| Flag | Result | Status | Reason |
|------|--------|--------|--------|
| no --online | - | SKIP | Offline |
| --online | all reachable | PASS | OK |
| --online | any fail | WARN | Unreachable |

---

## 5. Configuration

Environment variables (set in shell or .env):

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| OWNERSHIP_REQUIRED | 0/1 | 0 | Activate ownership check |
| ADR_REQUIRED | 0/1 | 0 | Activate ADR check |
| COVERAGE_MODE | "lite"/"off"/"full" | "lite" | Coverage heuristic level |
| SRC_DIRS | comma-list | "src,lib" | Directories to count as source |
| DOC_DIRS | comma-list | "docs" | Directories to count as docs |
| DOCS_SKILL_ENABLED | 1 | (unset) | Global enable (sentinel alternative) |

---

## 6. Signal Specifications

---

### 6A. Ownership Signal

**Definition**: Detects documentation files that lack an explicit owner.

**Detection Algorithm**:
1. Parse `.github/CODEOWNERS` (if exists) for patterns: `path @owner`
2. For each `.md` file in `docs/`, `*.md` (CLAUDE.md, README.md):
   - Check if path matches a CODEOWNERS pattern
   - If no match, check for `owner:` in YAML frontmatter
3. Output: list of docs without owner

**PARSING LIMITS (Phase 1 - Lite Parser)**:
- Supported: Exact paths, `*` wildcard, directory prefixes (e.g., `/docs/*`)
- NOT supported: `**` recursive, regex, multiple owners per line
- If CODEOWNERS has >10 patterns OR unsupported syntax:
  - OWNERSHIP_REQUIRED=0: INFO "CODEOWNERS too complex; use frontmatter owner"
  - OWNERSHIP_REQUIRED=1: WARN "CODEOWNERS too complex; add owner to doc frontmatter"

**Thresholds**:
- OWNERSHIP_REQUIRED=0: SKIP (not activated)
- OWNERSHIP_REQUIRED=1 + all docs owned: PASS
- OWNERSHIP_REQUIRED=1 + some docs unowned: WARN

**Status Mapping**:
- No CODEOWNERS, no frontmatter: INFO (no source)
- OWNERSHIP_REQUIRED=1 + all docs owned: PASS
- OWNERSHIP_REQUIRED=1 + some docs unowned: WARN

**Human Remediation**:
```
# Option 1: Add to CODEOWNERS
/docs/* @team-name

# Option 2: Add frontmatter to doc
---
owner: @team-name
---
```

**JSON Representation**:
```json
{
  "check": "ownership",
  "status": "WARN",
  "codeowners_rules": 2,
  "docs_covered": 5,
  "docs_uncovered": ["README.md", "CONTRIBUTING.md"]
}
```

---

### 6B. ADR Signal

**Definition**: Detects presence and freshness of Architecture Decision Records.

**Detection Algorithm**:
1. Check for directory: `docs/adr/` OR `docs/decisions/`
2. If exists:
   - Count `.md` files matching `ADR-NNN-*.md` or `NNN-*.md`
   - Find index file: `README.md` or `index.md` in ADR dir
   - Get latest ADR modification date via git (fallback: INFO if git fails)
3. If directory does not exist: SKIP (unless ADR_REQUIRED=1)

**INVARIANT**: ADR_REQUIRED=1 can emit FAIL. This is the only case where new signals can FAIL.

**Thresholds**:
- ADR_REQUIRED=0 + no dir: SKIP
- ADR_REQUIRED=0 + dir exists: INFO
- ADR_REQUIRED=1 + no dir: FAIL (explicit requirement not met)
- ADR_REQUIRED=1 OR dir exists + index missing: WARN
- Latest ADR >180 days old: WARN

**Status Mapping**:
- No ADR dir + ADR_REQUIRED=0: SKIP
- No ADR dir + ADR_REQUIRED=1: FAIL
- Dir exists + index exists + fresh (<=180d): PASS
- Dir exists + index missing: WARN
- Dir exists + stale >180d: WARN
- git log fails: INFO (determinism fallback)

**Human Remediation**:
```
# Create ADR directory
mkdir -p docs/adr

# Create index
echo "# ADRs" > docs/adr/README.md

# Add first ADR
echo "# ADR-001: Use Postgres" > docs/adr/ADR-001-postgres.md
```

**JSON Representation**:
```json
{
  "check": "adr",
  "status": "WARN",
  "adr_dir": "docs/adr",
  "adr_count": 3,
  "has_index": true,
  "latest_date": "2025-08-01",
  "days_old": 195
}
```

---

### 6C. Coverage-Lite Signal

**Definition**: Heuristic ratio of documentation files to source code files.

**Detection Algorithm**:
1. Expand SRC_DIRS (default: "src,lib") — exclude `__pycache__`, `node_modules`, `*.pyc`, `.git`, `dist`, `build`, `.venv`, `venv`
2. Expand DOC_DIRS (default: "docs") — exclude `_build`, `node_modules`, `.git`, `__pycache__`
3. **Content Filter**: Count only docs with >100 chars AND at least 1 heading OR 1 internal link
4. **Exclude meta-docs**: Do not count `LICENSE`, `LICENSE.md`, `CODE_OF_CONDUCT`, `CONTRIBUTING`, `CHANGELOG` (inflation protection)
5. Count files in each set
6. Calculate: `ratio = doc_count / src_count`
7. If no src files found: INFO (cannot compute)

**Anti-Gaming Rules**:
- Empty docs (<100 chars): not counted
- Meta-docs (LICENSE, CHANGELOG, etc.): not counted
- Must have meaningful content (heading OR link)

**Thresholds**:
- src_count = 0: INFO (no baseline)
- ratio < 0.05: WARN (critical gap)
- ratio 0.05-0.1: INFO (low but acceptable)
- ratio 0.1-0.3: PASS (healthy)
- ratio > 0.3: PASS (well-documented)

**Status Mapping**:
- No src files: INFO
- ratio < 0.05: WARN
- ratio 0.05-0.1: INFO
- ratio >= 0.1: PASS

**Human Remediation**:
```
# Increase docs coverage
- Add README.md to each new module
- Document public APIs
- Create docs/adr/ for architecture decisions
```

**JSON Representation**:
```json
{
  "check": "coverage_lite",
  "status": "PASS",
  "doc_count": 15,
  "src_count": 120,
  "ratio": 0.12,
  "src_dirs": ["src", "lib"],
  "doc_dirs": ["docs"]
}
```

---

### 6D. External Links Signal

**Detection Algorithm**:
1. Extract URLs from markdown links: `[text](http...)`
2. If --online NOT set: SKIP (do not test)
3. If --online set: curl each URL with 5s timeout
4. Count failures

**Thresholds**:
- Offline (no --online): SKIP
- Online + all reachable: PASS
- Online + any unreachable: WARN

**Status Mapping**:
- No --online: SKIP
- --online + 0 failures: PASS
- --online + N failures: WARN

**JSON Representation**:
```json
{
  "check": "external_links",
  "status": "SKIP",
  "reason": "offline"
}
```

---

## 7. Evidence Pack

### Case 1: SKIP (no sentinel)
```bash
$ bash verify_documentation.sh .
ℹ️  SKIP: Documentation skill not enabled
      Enable: touch .documentation-skill.enabled or DOCS_SKILL_ENABLED=1
Exit: 0
```

### Case 2: RUN offline (no --online)
```bash
$ bash verify_documentation.sh . --force
🔍 Validating Agent Documentation Pattern...

[✓] PASS: file_exists
[✓] PASS: critical_section
[✓] PASS: proceed_phrase
[✓] PASS: mandatory_files
[✓] PASS: time_estimates
[✓] PASS: skip_section
[✓] PASS: consequences
[✓] PASS: absolute_paths
[✓] PASS: local_links
[→] SKIP: external_links (use --online to check)
[✓] PASS: critical_position
[✓] PASS: staleness
[✓] PASS: ctx_references

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: ALLOW
  └─ Core: 0 FAIL, 0 WARN | Overmind: 0 FAIL, 0 WARN

Health Score: 85/100 (FYI only)
Summary: 12 PASS, 0 WARN, 0 FAIL, 1 INFO, 0 SKIP
```

### Case 3: RUN with ownership + coverage WARNs
```bash
$ OWNERSHIP_REQUIRED=1 bash verify_documentation.sh . --force
...
[⚠] WARN: ownership (9 docs without owner - covered: 0/9)
[→] SKIP: adr (No ADR directory found - set ADR_REQUIRED=1 to enable)
[✓] PASS: coverage (237 docs / 65 src = 0.364 ratio)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: ALLOW
  └─ Core: 0 FAIL, 0 WARN | Overmind: 0 FAIL, 2 WARN

Health Score: 90/100 (FYI only)
Summary: 13 PASS, 2 WARN, 0 FAIL, 1 INFO, 1 SKIP
```

### Case 4: RUN with --online (external links WARN)
```bash
$ bash verify_documentation.sh . --force --online
...
[⚠] WARN: external_links (3 unreachable links)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: ALLOW
  └─ Core: 0 FAIL, 1 WARN | Overmind: 0 FAIL, 0 WARN

Health Score: 70/100 (FYI only)
```

### Case 5: FAIL blocking commit
```bash
$ bash verify_documentation.sh . --force
...
[✗] FAIL: critical_section (CLAUDE.md missing CRITICAL section)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: BLOCK (1 FAIL)
  └─ Core: 1 FAIL, 0 WARN | Overmind: 0 FAIL, 0 WARN

Health Score: 40/100 (FYI only)
Summary: 5 PASS, 0 WARN, 3 FAIL, 0 INFO, 0 SKIP
❌ BLOCKED: Fix failures before committing
```

### Case 3: RUN with ownership + coverage WARNs
```bash
$ OWNERSHIP_REQUIRED=1 bash verify_documentation.sh . --force
...
[⚠] WARN: ownership (2 docs uncovered: README.md, CONTRIBUTING.md)
[⚠] WARN: coverage_lite (0.03 ratio - critical gap)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: ALLOW (no FAIL, WARNs don't block)
Health Score: 75/100 (FYI only)
Summary: 12 PASS, 2 WARN, 0 FAIL
```

### Case 4: RUN with --online (external links WARN)
```bash
$ bash verify_documentation.sh . --force --online
...
[⚠] WARN: external_links (3 unreachable links)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: ALLOW (no FAIL)
Health Score: 70/100 (FYI only)
```

### Case 5: FAIL blocking commit
```bash
$ bash verify_documentation.sh . --force
...
[✗] FAIL: critical_section (CLAUDE.md missing CRITICAL section)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate Verdict: BLOCK (FAIL detected)
Health Score: 40/100 (FYI only)
Summary: 5 PASS, 0 WARN, 3 FAIL
❌ BLOCKED: Fix failures before committing
```

---

## 8. DoD (Definition of Done)

### Ownership Signal
- [ ] Respects OWNERSHIP_REQUIRED config (0=skip, 1=check)
- [ ] Parses CODEOWNERS for ownership patterns
- [ ] Falls back to frontmatter owner
- [ ] Outputs correct status: SKIP/INFO/PASS/WARN
- [ ] JSON includes: check, status, codeowners_rules, docs_covered, docs_uncovered

### ADR Signal
- [ ] Respects ADR_REQUIRED config (0=skip if no dir, 1=force)
- [ ] Detects docs/adr/ OR docs/decisions/
- [ ] Validates index existence
- [ ] Checks staleness via git (not file date)
- [ ] Correct status: SKIP/PASS/WARN
- [ ] JSON includes: check, status, adr_count, has_index, latest_date, days_old

### Coverage-Lite Signal
- [ ] Respects COVERAGE_MODE (off/lite/full)
- [ ] Excludes generated dirs: __pycache__, node_modules, .git, _build
- [ ] Respects SRC_DIRS and DOC_DIRS config
- [ ] Handles zero src files (INFO, not WARN)
- [ ] Correct thresholds: <0.05 WARN, 0.05-0.1 INFO, >=0.1 PASS
- [ ] JSON includes: check, status, doc_count, src_count, ratio

### External Links
- [ ] SKIP when offline (no --online flag)
- [ ] WARN only with --online flag
- [ ] Timeout: 5 seconds per URL

### Health Score
- [ ] Score is FYI only (informational)
- [ ] Single blocking rule: FAIL blocks, WARN does NOT (unless --strict)
- [ ] Formula: 100 - 15*FAIL - 5*WARN (display only)
- [ ] SKIP exits cleanly (code 0)

### JSON Contract
- [ ] schema_version: "1.0"
- [ ] run_id: timestamp or UUID
- [ ] repo_root: absolute path
- [ ] Duration tracking: duration_ms per check
- [ ] Gate verdict: { "block": bool, "reasons": [...] }
- [ ] Counts: { "pass": n, "warn": n, "fail": n, "info": n, "skip": n }
- [ ] Breakdown: { "core_errors": n, "core_warnings": n, "overmind_errors": n, "overmind_warnings": n }
- [ ] Per-check fields: check, status, summary, evidence[], remediation

**JSON Schema v1.0**:
```json
{
  "schema_version": "1.0",
  "run_id": "2026-02-15T10:30:00Z",
  "repo_root": "/path/to/repo",
  "timestamp": "2026-02-15T10:30:00Z",
  "duration_ms": 1234,
  "verdict": {
    "block": false,
    "reasons": []
  },
  "counts": {
    "pass": 12,
    "warn": 2,
    "fail": 0,
    "info": 1,
    "skip": 0
  },
  "breakdown": {
    "core_errors": 0,
    "core_warnings": 0,
    "overmind_errors": 0,
    "overmind_warnings": 2
  },
  "score": 85,
  "checks": [
    {
      "check": "ownership",
      "status": "WARN",
      "summary": "2 docs without owner",
      "evidence": ["README.md", "CONTRIBUTING.md"],
      "remediation": "Add owner: @team to frontmatter",
      "duration_ms": 45
    }
  ]
}
```

### WO Prohibition
- [ ] Ignores _ctx/, _ctx/jobs/, _ctx/backlog/
- [ ] Ignores WO-*.yaml, backlog.yaml
- [ ] Returns SKIP for WO paths (never WARN/FAIL)

---

## 9. Risks & Anti-Spam Guards

### WO Prohibition (Hard Guard)
The script MUST ignore/prohibit WO-related paths:
- `_ctx/`, `_ctx/jobs/`, `_ctx/backlog/`
- `WO-*.yaml`, `backlog.yaml`
- Any check targeting WO system: FAIL with message "WO scope prohibited"

Implementation: Paths matching these patterns always emit SKIP, never WARN/FAIL.

### Warning Fatigue Prevention
1. **Opt-in by default**: Signals only activate with config or sentinel
2. **No universal WARNs**: Every WARN is actionable with clear remediation
3. **INFO level**: Non-blocking FYIs for borderline cases
4. **Single blocking rule**: FAIL blocks, WARN does NOT (unless --strict)
5. **Configurable**: Users can disable noisy checks

### False Positive Prevention
- Coverage-lite: Excludes generated code (node_modules, __pycache__)
- Ownership: Requires explicit activation (OWNERSHIP_REQUIRED=1)
- Ownership CODEOWNERS: Lite parser with "too complex" fallback to INFO
- ADR: Requires dir existence OR explicit activation
- External links: SKIP offline, WARN only online
- git log fails: INFO (not FAIL)

### Determinism Guarantees
- CODEOWNERS: Lite pattern matching only (no git queries)
- Coverage: File system only, no network
- ADR: Git history for staleness (INFO fallback if git fails)
- External: Network-dependent by design, opt-in only
