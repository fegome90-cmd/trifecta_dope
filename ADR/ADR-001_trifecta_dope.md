ADR-001: Micro-Audit Patterns Scan Before Feature Work

Status: Proposed (ready to adopt)

Date: 2026-01-02

Context: Trifecta (CLI: ctx sync/search/get; AST-first; LSP as enhancement; auditable telemetry)

Decision

Before starting any new feature or “hardening” work, we will run a Micro-Audit Scan to detect a known set of failure patterns that historically turn “small fixes” into long audit/correction loops.

This scan is mandatory when changes touch CLI behavior, lifecycle/shutdown, telemetry/auditing, test infrastructure, or env/flag configuration.

Why

We repeatedly lost hours to micro-bugs with structural impact:

string-based parsing/classification that breaks under refactors

non-deterministic tests (repo-real, SKIP, cwd/tmp sensitivity)

accidental cwd/path coupling causing failures only in agents/CI

shutdown races and stderr noise in concurrency/subprocess code

env/flag defaults without a precedence contract

These are predictable and preventable. The Micro-Audit Scan turns them into a preflight gate and a micro-task backlog.

Patterns We Must Scan For
P1 — Stringly-Typed Contracts (Parsing / Classification)

Symptoms

startswith(...), "... in error_msg", parsing stdout text

classification based on substrings (e.g., "Expected prime file not found")

Risk

brittle behavior; cosmetic refactors break core logic

Preferred Mitigation

Single Source of Truth (SST) parser functions

type-based exceptions (custom exception classes)

versioned / key-invariant contract outputs (PD_REPORT, JSON)

P2 — Non-Deterministic Test Oracles

Symptoms

tests depend on repo-real state, network, filesystem telemetry presence

SKIP/XFAIL for “local only”

assertions that only check return code, not invariants

Risk

false green, CI flakes, regressions not caught

Preferred Mitigation

deterministic tmp-segment acceptance tests

contract outputs (PD_REPORT v=1)

tripwire assertions (“must_not_contain”, “single-occurrence”, “last-line”)

P3 — CWD / Path Coupling

Symptoms

Path.cwd(), os.getcwd(), relative _ctx/ paths

writing artifacts in CLI cwd instead of segment_root

Risk

works in manual runs, fails in harness/agents/CI

Preferred Mitigation

“Path Discipline”: resolve all IO against segment_root

acceptance tests that run from different cwd

P4 — Concurrency & Shutdown Noise

Symptoms

“write to closed file”

thread join ordering issues

subprocess terminate/kill without stop signals/guards

Risk

stderr noise, flakes, corrupted evidence; hard-to-debug races

Preferred Mitigation

lifecycle hardening: stop flag → terminate → join → close

tripwire tests for forbidden stderr strings

P5 — Env/Flag Defaults Without Precedence Contract

Symptoms

conflicting env vars/flags

implicit defaults that vary by environment

“invalid policy treated differently”

Risk

unpredictable behavior; debugging time sink

Preferred Mitigation

documented precedence table (default → env → flag)

tests for default/override/invalid values

explicit policy enums (off|warn|fail)

Process
When Required

Run the Micro-Audit Scan when:

modifying CLI output/flags/env policies

touching telemetry or _ctx/ paths

changing error handling / classification

touching subprocess/thread lifecycle

adding/modifying acceptance tests

Outputs

The scan produces a MICRO_AUDIT_REPORT.md with:

Top 10 findings ordered by ROI

for each finding: signal (rg query), path:line, risk, fix lean (≤60 lines), tripwire test, evidence commands

flags/env precedence table (TRIFECTA_*)

list of SKIP/XFAIL tests and deterministic replacements

Definition of Done for Fixes

Any fix addressing these patterns must include:

at least one deterministic test (unit/acceptance) or

a contract output with regression coverage (e.g., PD_REPORT last-line + single-occurrence)

evidence commands and raw outputs for auditability

Consequences
Positive

reduces audit/correction loops

prevents “works locally” failures

increases determinism, auditability, and developer velocity

Costs / Tradeoffs

small up-front time to run the scan and write micro-tasks

slightly stricter PR discipline (tests + evidence required)

Appendix: Micro-Audit Scan Commands (v1)

Run from repo root (exclude .venv, _ctx):

Stringly parsing/classification

rg -n --hidden --glob '!**/.venv/**' --glob '!**/_ctx/**' \
  'startswith\(|endswith\(|in error_msg|in str\(e\)|"Expected .* not found"|split\(|lower\(\)' \
  src tests


CWD / paths

rg -n --hidden --glob '!**/.venv/**' --glob '!**/_ctx/**' \
  'Path\.cwd\(\)|os\.getcwd\(\)|chdir\(|\b\./_ctx\b|_ctx/|relative_to\(' \
  src tests scripts


SKIP/XFAIL/flaky

rg -n --hidden --glob '!**/.venv/**' \
  '@pytest\.mark\.skip|pytest\.skip|xfail|flaky|random|time\.sleep|local only|CI' \
  tests


Flags/env

rg -n --hidden --glob '!**/.venv/**' \
  'os\.environ|getenv\(|TRIFECTA_|--[a-z0-9_-]+' \
  src tests


Concurrency/shutdown

rg -n --hidden --glob '!**/.venv/**' \
  'threading\.Thread|daemon=True|join\(|terminate\(|kill\(|wait\(|BrokenPipeError|write to closed file|ValueError: I/O operation on closed file|OSError' \
  src tests
