# LSP Daemon Follow-up Batches

**Original plan date:** 2026-03-26
**Documentation status:** historical and operational reference
**Current state at HEAD:** Batches 2A-2C completed; Batch 2D deferred

## Purpose and scope

This document preserves the outcome of the 2026-03-26 LSP daemon follow-up plan after the branch work landed. It is intended to remain as durable repository documentation, not as a live handoff or pending-task checklist.

Scope is limited to the post-hardening follow-up around daemon authority, LSP client shutdown hygiene, and READY/readiness semantics. It records what was completed, what evidence exists in the repository, and what remains intentionally out of scope.

## Baseline and prior commits

The follow-up work built on the earlier daemon hardening already present on the branch:

- `7640291` — `fix(lsp-daemon): harden lifecycle and handler contracts`
- `e358eee` — `fix(daemon-manager): harden lock and shutdown verification`
- `ca87b30` — `docs(plan): add lsp daemon follow-up batches`

The original `ca87b30` document described remaining work. This version records the final disposition of that work after the later fixes landed.

## Follow-up batches summary

### Batch 2A — completed (`b355926`)

**Commit:** `b355926` — `fix(daemon-manager): remove proxy-based liveness checks`

**What changed**
- `DaemonManager.status()` and `is_running()` now require a live PID plus socket presence before reporting the daemon as running.
- `_acquire_singleton_lock()` no longer recovers an old lock purely because it aged out; it first checks for live PID evidence and only treats the lock as stale when authority evidence is absent.
- The daemon-manager surface now uses process liveness as the primary authority signal, with socket presence as supporting evidence rather than a proxy for truth.

**Affected files**
- `src/platform/daemon_manager.py`
- `tests/unit/test_daemon_manager.py`

### Batch 2B — completed (`0771d74`)

**Commit:** `0771d74` — `fix(lsp-client): clear lifecycle residue on stop`

**What changed**
- `LSPClient.stop()` now clears shutdown residue after a clean stop instead of leaving stale runtime state behind.
- Cleanup now closes process streams, releases pending request waiters, and resets `process`, `_thread`, capability state, request tracking, and warmup-file state.
- The stop path remains idempotent and can finish cleanup on a later call if an earlier join attempt timed out.

**Affected files**
- `src/infrastructure/lsp_client.py`
- `tests/unit/test_lsp_client_strict.py`

### Batch 2C — completed (`205f21e`)

**Commit:** `205f21e` — `fix(lsp): align readiness semantics and daemon parity`

**What changed**
- READY semantics were made explicit: the historical invariant name `health_check_responds` remains, but the READY gate now passes when the initialize response includes a `capabilities` field, even if that field is an empty object.
- `LSPClient` now tracks whether capabilities were received separately from whether the capabilities payload is truthy, preventing empty `{}` responses from being treated as readiness failure.
- `src/infrastructure/lsp_daemon.py` now treats `None` as the real “no result” signal and preserves `{}` as a valid LSP response, keeping daemon-side behavior aligned with the client contract.
- The contract documentation was updated to match the implemented behavior.

**Affected files**
- `docs/contracts/LSP_READY_INVARIANTS.md`
- `src/infrastructure/lsp_client.py`
- `src/infrastructure/lsp_daemon.py`
- `tests/unit/test_lsp_ready_contract.py`

### Batch 2D — deferred / out of current scope

**Surface:** `src/platform/runtime_manager.py`

Batch 2D was intentionally left out of this follow-up series.

**Why it was deferred**
- The authority and readiness issues identified in the 2026-03-26 review were resolved without needing `runtime_manager.py` changes.
- No small, high-confidence, low-blast-radius correction was required in that file to make the daemon path truthful at this stage.
- Pulling it into the same remediation would have expanded scope beyond the fixes that were already justified by current behavior and tests.

**When to reopen**
- Reconsider Batch 2D only if `runtime_manager.py` becomes an active authority surface again, or if a narrowly scoped contract-alignment change can be proven with focused tests and limited blast radius.

## Verification and evidence references

Primary repository evidence for the completed follow-up work:

- `b355926` — daemon-manager authority cleanup
- `0771d74` — LSP client stop residue cleanup
- `205f21e` — readiness semantics and daemon parity

Relevant durable references:

- `docs/contracts/LSP_READY_INVARIANTS.md`
- `tests/unit/test_daemon_manager.py`
- `tests/unit/test_lsp_client_strict.py`
- `tests/unit/test_lsp_ready_contract.py`

Focused revalidation commands for this follow-up surface:

```bash
uv run pytest \
  tests/unit/test_daemon_manager.py \
  tests/unit/test_lsp_client_strict.py \
  tests/unit/test_lsp_ready_contract.py -q

uvx ruff check \
  src/platform/daemon_manager.py \
  src/infrastructure/lsp_client.py \
  src/infrastructure/lsp_daemon.py \
  docs/contracts/LSP_READY_INVARIANTS.md \
  tests/unit/test_daemon_manager.py \
  tests/unit/test_lsp_client_strict.py \
  tests/unit/test_lsp_ready_contract.py

uv run mypy \
  src/platform/daemon_manager.py \
  src/infrastructure/lsp_client.py \
  src/infrastructure/lsp_daemon.py --strict
```

## Current status and next considerations

At current HEAD, the follow-up batches originally tracked as 2A, 2B, and 2C are complete and reflected in code, tests, and contract documentation. The original planning document is therefore best preserved as a historical record of what changed, not as an active checklist.

No additional daemon-manager, LSP client shutdown, or READY semantics work is required to preserve this document as official repository documentation. The only explicitly open consideration from the original batch list is Batch 2D, which remains deferred and should stay outside current completion claims unless it is separately re-scoped.
