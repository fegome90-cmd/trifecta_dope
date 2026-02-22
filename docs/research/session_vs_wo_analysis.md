# Research Report: Work Sessions (GitHub) vs. Work Orders (Trifecta)

## Executive Summary

This report provides a comparative analysis between the **Work Session** system implementation found in the [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) repository and the local **Work Orders (WO)** system in Trifecta.

### Verdict

While both systems aim to solve agentic continuity and context management, they represent two distinct philosophies:

1. **Work Sessions (Oh-My-Opencode)**: An **operational-centric** system designed for seamless flow, context window preservation, and multi-backend persistence (SQLite/Cloud). It prioritizes the "Developer Experience" of the agent.
2. **Work Orders (Trifecta)**: An **audit-centric** system designed as a "Workflow as a Contract." It prioritizes deterministic execution, safety (via worktrees), and immutable proof-of-work (DoD).

---

## 1. System Decomposition

### A. Trifecta Work Orders (Local)

Trifecta manages work as discrete, governed units.

- **Primary Entity**: `WorkOrder` (YAML-based)
- **Isolation Mechanism**: Git Worktrees. Each task runs in a physically isolated directory.
- **State Machine**: Strict transition logic (`PENDING -> RUNNING -> DONE/FAILED`).
- **Governance**: `backlog.yaml` serves as the Single Source of Truth for project milestones (Epics).
- **Proof of Work**: Requires a `verdict.json` and a `diff.patch` for closure.
- **Recent Evolution**: The system has recently moved toward a more **minimalist** implementation, removing complex "audit-grade" features like patch hashing and transaction-level cleanup to reduce overhead.

### B. oh-my-opencode Work Sessions (GitHub)

The Sisyphus agent uses sessions to manage continuity.

- **Primary Entity**: `Session` (JSON-based) indexed by `sessionID`.
- **Glue Mechanism**: `boulder.json` tracks plan status and session history within a project.
- **Context Management**: The `handoff` command explicitly summarizes programmatic state (files, tasks, plans) to "refresh" the context window without losing intent.
- **Persistence**: High flexibility with support for local files, SQLite databases, and cloud-based SDK storage.
- **Interface**: Uses slash-commands (`/start-work`, `/handoff`, `/stop-continuation`) to drive the lifecycle.

---

## 2. Comparative Matrix

| Category | Trifecta Work Orders | oh-my-opencode Work Sessions |
| :--- | :--- | :--- |
| **Philosophy** | "Audit-Grade" (Execution as Contract) | "Continuity-Grade" (Flow focus) |
| **State Storage** | Filesystem (`_ctx/jobs/`) | Multi-backend (SQLite/JSON/Cloud) |
| **Isolation** | Physical (Worktrees) | Logical (Session Contexts) |
| **Planning** | Pre-defined in `backlog.yaml` | Dynamic Markdown Plans (`.sisyphus/`) |
| **Handoff** | DoD Artifacts (Terminal) | Handoff Context (Transitionary) |
| **Complexity** | High (Policy-driven) | Medium (Tool-driven) |
| **Main Use Case**| Mission-critical code changes | Long-running research/refactoring |

---

## 3. Pattern Analysis

### Shared Patterns

- **State Machines**: Both systems use deterministic states to prevent "lost agents."
- **Persistence Files**: Both use a repo-local file (`backlog.yaml` vs `boulder.json`) to anchor the agent's memory to the repository state.
- **Structured Intent**: Both require an "Intent" (Objective) to be defined before execution.

### Key Divergences

- **The "Worktree" Boundary**: Trifecta's use of worktrees is its most significant differentiator. It prevents agents from polluting the `main` branch state during messy refactors. Oh-my-opencode operates directly on the current branch.
- **Context Refresh vs. DoD closure**: oh-my-opencode focuses on *extending* the agent's life via handoffs. Trifecta focuses on *verifying* the agent's work via DoD gates.

---

## 4. Integration & Strategic Recommendations

### Compatibility Assessment

The two systems are conceptually compatible but solve different parts of the SDLC. Trifecta is excellent for **merging** quality code, while Oh-My-Opencode is superior for **maintaining** long-running thought processes.

### Recommendations for Trifecta

1. **Adopt the Handoff Pattern**: Trifecta could benefit from a "warm handoff" tool like oh-my-opencode’s when a Work Order exceeds the context limit.
2. **Multi-backend Support**: Migrating `backlog.yaml` tracking to a SQLite-backed index (similar to oh-my-opencode) would improve performance for massive registries.

### Recommendations for oh-my-opencode patterns

1. **Worktree Guardrails**: Integrating Trifecta's worktree isolation would prevent "dirty state" issues when complex sessions fail.
2. **DoD Schemas**: Standardizing handoff summaries into a formal "Verdict" schema (like Trifecta) would make the system more auditable.

---

## 5. Investigation Evidence

Below is the recording of the automated investigation of the `oh-my-opencode` repository.

![Investigation Recording](file:///Users/felipe_gonzalez/.gemini/antigravity/brain/6f4adf0b-76ad-43bd-9f68-802579f8b0ba/investigate_oh_my_opencode_1771773336633.webp)

---
**Report compiled by:** Senior Systems Analyst (Antigravity)
**Date**: 2026-02-22
